from django.shortcuts import render
from rest_framework import status
from rest_framework.decorators import api_view, permission_classes
from rest_framework.permissions import AllowAny
from rest_framework.response import Response
from django.db import transaction
from .models import Client, TallyTransaction, LedgerEntry, LedgerOpeningBalance
import json
from datetime import datetime
from django.db import models  # type: ignore
from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework import status, permissions, authentication
from django.contrib.auth import get_user_model
from rest_framework.authtoken.models import Token
from django.db import transaction as db_transaction
import logging

# Create your views here.

@api_view(['POST'])
@permission_classes([AllowAny])
def receive_tally_transactions(request):
    """
    Receive Tally transactions from the sync agent and store them grouped by client, including all ledger entries.
    """
    import logging
    logger = logging.getLogger('tally_transaction_import')
    try:
        data = request.data
        if not isinstance(data, list):
            logger.error('Payload is not a list')
            return Response({'error': 'Data must be a list of transactions'}, status=status.HTTP_400_BAD_REQUEST)
        transactions_created = 0
        clients_created = 0
        errors = []
        with transaction.atomic():
            for idx, transaction_data in enumerate(data):
                party_name = transaction_data.get('party_name', '').strip()
                if not party_name:
                    errors.append(f'Transaction {idx}: Missing party_name')
                    continue
                client, created = Client.objects.get_or_create(name=party_name, defaults={'address': ''})
                if created:
                    clients_created += 1
                # Parse date from YYYYMMDD
                date_str = transaction_data.get('date', '')
                date_obj = None
                if date_str:
                    try:
                        if len(date_str) == 8 and date_str.isdigit():
                            date_obj = datetime.strptime(date_str, '%Y%m%d').date()
                        elif '/' in date_str:
                            date_obj = datetime.strptime(date_str, '%d/%m/%Y').date()
                        else:
                            date_obj = datetime.strptime(date_str, '%Y-%m-%d').date()
                    except Exception as ex:
                        logger.warning(f'Transaction {idx}: Invalid date format {date_str}, using today. Error: {ex}')
                        date_obj = datetime.now().date()
                else:
                    date_obj = datetime.now().date()
                # Map voucher_type to register_type
                voucher_type = transaction_data.get('voucher_type', '').lower()
                register_type_map = {
                    'sales': 'sales',
                    'purchase': 'purchase',
                    'payment': 'payment',
                    'receipt': 'receipt',
                    'journal': 'journal',
                    'credit note': 'credit_note',
                    'debit note': 'debit_note',
                }
                register_type = register_type_map.get(voucher_type, 'journal')
                # Handle amount: if blank, sum ledger entries
                amount = transaction_data.get('amount', None)
                if amount in [None, '', ' ']:
                    try:
                        amount = sum(float(le.get('amount', 0.0) or 0.0) for le in transaction_data.get('ledger_entries', []))
                    except Exception as ex:
                        logger.error(f'Transaction {idx}: Error summing ledger entry amounts: {ex}')
                        amount = 0.0
                else:
                    try:
                        amount = float(amount)
                    except Exception as ex:
                        logger.error(f'Transaction {idx}: Invalid amount {amount}, using 0. Error: {ex}')
                        amount = 0.0
                try:
                    txn = TallyTransaction.objects.create(
                        voucher_no=transaction_data.get('voucher_no', ''),
                        date=date_obj,
                        party_name=party_name,
                        narration=transaction_data.get('narration', ''),
                        amount=amount,
                        register_type=register_type,
                        client=client
                    )
                except Exception as ex:
                    logger.error(f'Transaction {idx}: Error creating TallyTransaction: {ex}')
                    errors.append(f'Transaction {idx}: Error creating TallyTransaction: {ex}')
                    continue
                # Save all ledger entries for this transaction
                for le_idx, le in enumerate(transaction_data.get('ledger_entries', [])):
                    le_amount = le.get('amount', 0.0)
                    try:
                        le_amount = float(le_amount)
                    except Exception as ex:
                        logger.warning(f'Transaction {idx} LedgerEntry {le_idx}: Invalid amount {le_amount}, using 0. Error: {ex}')
                        le_amount = 0.0
                    try:
                        LedgerEntry.objects.create(
                            transaction=txn,
                            ledger_name=le.get('ledger_name', ''),
                            amount=le_amount,
                            is_debit=le.get('is_debit', False),
                            is_credit=le.get('is_credit', False),
                            raw_data=le.get('all_fields', le.get('raw_data', {}))
                        )
                    except Exception as ex:
                        logger.error(f'Transaction {idx} LedgerEntry {le_idx}: Error creating LedgerEntry: {ex}')
                        errors.append(f'Transaction {idx} LedgerEntry {le_idx}: Error creating LedgerEntry: {ex}')
                transactions_created += 1
        response_data = {
            'message': 'Transactions processed successfully',
            'transactions_created': transactions_created,
            'clients_created': clients_created,
            'errors': errors
        }
        logger.info(f'Import summary: {response_data}')
        return Response(response_data, status=status.HTTP_201_CREATED)
    except Exception as e:
        logger.critical(f'Critical error processing transactions: {e}')
        return Response({'error': f'Error processing transactions: {str(e)}'}, status=status.HTTP_500_INTERNAL_SERVER_ERROR)

@api_view(['GET'])
@permission_classes([AllowAny])
def get_client_transactions(request, client_name=None):
    """
    Get all transactions for a specific client
    """
    try:
        if client_name:
            # Get transactions for specific client
            transactions = TallyTransaction.objects.filter(  # type: ignore
                party_name__icontains=client_name
            ).select_related('client')
        else:
            # Get all transactions grouped by client
            transactions = TallyTransaction.objects.all().select_related('client')  # type: ignore
        
        # Group by client
        client_data = {}
        for trans in transactions:
            client_name = trans.party_name
            if client_name not in client_data:
                client_data[client_name] = {
                    'client_name': client_name,
                    'total_transactions': 0,
                    'total_amount': 0.0,
                    'transactions': []
                }
            
            client_data[client_name]['total_transactions'] += 1
            client_data[client_name]['total_amount'] += float(trans.amount)
            client_data[client_name]['transactions'].append({
                'id': trans.id,
                'voucher_no': trans.voucher_no,
                'date': trans.date.isoformat(),
                'narration': trans.narration,
                'amount': float(trans.amount),
                'register_type': trans.register_type,
                'created_at': trans.created_at.isoformat()
            })
        
        return Response({
            'clients': list(client_data.values())
        }, status=status.HTTP_200_OK)
        
    except Exception as e:
        return Response(
            {'error': f'Error retrieving transactions: {str(e)}'}, 
            status=status.HTTP_500_INTERNAL_SERVER_ERROR
        )

@api_view(['GET'])
@permission_classes([AllowAny])
def get_clients_summary(request):
    """
    Get summary of all clients with their transaction counts and amounts
    """
    try:
        clients = Client.objects.annotate(  # type: ignore
            transaction_count=models.Count('transactions'),
            total_amount=models.Sum('transactions__amount')
        ).values('name', 'transaction_count', 'total_amount')
        
        return Response({
            'clients': list(clients)
        }, status=status.HTTP_200_OK)
        
    except Exception as e:
        return Response(
            {'error': f'Error retrieving clients summary: {str(e)}'}, 
            status=status.HTTP_500_INTERNAL_SERVER_ERROR
        )

@api_view(['POST'])
@permission_classes([AllowAny])
def receive_opening_balances(request):
    """
    Receive opening balances from the agent and store them for each client.
    """
    try:
        data = request.data
        if not isinstance(data, list):
            return Response({'error': 'Data must be a list of opening balances'}, status=status.HTTP_400_BAD_REQUEST)
        balances_created = 0
        clients_created = 0
        with transaction.atomic():
            for bal in data:
                client_name = bal.get('client_name', '').strip() or bal.get('company_name', '').strip()
                if not client_name:
                    continue
                client, created = Client.objects.get_or_create(name=client_name, defaults={'address': ''})
                if created:
                    clients_created += 1
                LedgerOpeningBalance.objects.create(
                    client=client,
                    ledger_name=bal.get('ledger_name', ''),
                    opening_balance=bal.get('opening_balance', 0.0),
                    group=bal.get('group', ''),
                    raw_balance=bal.get('raw_balance', '')
                )
                balances_created += 1
        return Response({
            'message': 'Opening balances processed successfully',
            'balances_created': balances_created,
            'clients_created': clients_created
        }, status=status.HTTP_201_CREATED)
    except Exception as e:
        return Response({'error': f'Error processing opening balances: {str(e)}'}, status=status.HTTP_500_INTERNAL_SERVER_ERROR)

class TokenHeaderAuthentication(authentication.TokenAuthentication):
    keyword = 'Bearer'

    def authenticate(self, request):
        from .models import Token, User
        auth = authentication.get_authorization_header(request).split()
        if not auth or auth[0].lower() != b'bearer':
            return None
        if len(auth) == 1:
            return None
        elif len(auth) > 2:
            return None
        try:
            token_key = auth[1].decode()
        except UnicodeError:
            return None
        try:
            token_obj = Token.objects.select_related('user').get(key=token_key)
        except Token.DoesNotExist:
            return None
        if not token_obj.user.is_active:
            return None
        return (token_obj.user, token_obj)

logger = logging.getLogger("cfa.transactions")

class TransactionUploadView(APIView):
    authentication_classes = [TokenHeaderAuthentication]
    permission_classes = [permissions.IsAuthenticated]

    def post(self, request):
        user = request.user
        client = getattr(user, 'client', None)
        if not client:
            return Response({'error': 'User is not associated with a client.'}, status=400)
        data = request.data
        tx_list = data if isinstance(data, list) else data.get('data', [])
        if not isinstance(tx_list, list):
            return Response({'error': 'Invalid data format.'}, status=400)
        created = 0
        skipped = 0
        errors = []
        with db_transaction.atomic():
            for idx, tx in enumerate(tx_list):
                party_name = tx.get('party_name') or tx.get('client_name') or 'Unknown'
                voucher_no = tx.get('voucher_no') or tx.get('voucher_number') or f'V{idx+1}'
                voucher_type = (tx.get('voucher_type') or tx.get('register_type') or 'journal').lower()
                date_str = tx.get('date', '')
                narration = tx.get('narration', '')
                amount = tx.get('amount', None)
                ledger_entries = tx.get('ledger_entries') or tx.get('entries') or []
                # Parse date
                date_obj = None
                try:
                    if date_str and len(date_str) == 8 and date_str.isdigit():
                        date_obj = datetime.strptime(date_str, '%Y%m%d').date()
                    elif date_str and '/' in date_str:
                        date_obj = datetime.strptime(date_str, '%d/%m/%Y').date()
                    elif date_str:
                        date_obj = datetime.strptime(date_str, '%Y-%m-%d').date()
                    else:
                        date_obj = datetime.now().date()
                except Exception as ex:
                    logger.warning(f"Transaction {idx}: Invalid date format {date_str}, using today. Error: {ex}")
                    date_obj = datetime.now().date()
                # Map voucher_type to register_type
                register_type_map = {
                    'sales': 'sales',
                    'purchase': 'purchase',
                    'payment': 'payment',
                    'receipt': 'receipt',
                    'journal': 'journal',
                    'credit note': 'credit_note',
                    'debit note': 'debit_note',
                }
                register_type = register_type_map.get(voucher_type, 'journal')
                # Handle amount: if blank, sum ledger entries
                if amount in [None, '', ' ']:
                    try:
                        amount = sum(float(le.get('amount', 0.0) or 0.0) for le in ledger_entries)
                    except Exception as ex:
                        logger.error(f'Transaction {idx}: Error summing ledger entry amounts: {ex}')
                        amount = 0.0
                else:
                    try:
                        amount = float(amount)
                    except Exception as ex:
                        logger.error(f'Transaction {idx}: Invalid amount {amount}, using 0. Error: {ex}')
                        amount = 0.0
                # Check for duplicate transaction
                duplicate = TallyTransaction.objects.filter(
                    voucher_no=voucher_no,
                    date=date_obj,
                    party_name=party_name,
                    register_type=register_type
                ).first()
                if duplicate:
                    logger.info(f"Skipping duplicate transaction at idx {idx}: {voucher_no}, {date_obj}, {party_name}, {register_type}")
                    skipped += 1
                    errors.append({'idx': idx, 'reason': 'duplicate transaction'})
                    continue
                try:
                    t = TallyTransaction.objects.create(
                        client=client,
                        voucher_no=voucher_no,
                        date=date_obj,
                        party_name=party_name,
                        narration=narration,
                        amount=amount,
                        register_type=register_type,
                    )
                    for le_idx, le in enumerate(ledger_entries):
                        le_amount = le.get('amount', 0.0)
                        try:
                            le_amount = float(le_amount)
                        except Exception as ex:
                            logger.warning(f'Transaction {idx} LedgerEntry {le_idx}: Invalid amount {le_amount}, using 0. Error: {ex}')
                            le_amount = 0.0
                        LedgerEntry.objects.create(
                            transaction=t,
                            ledger_name=le.get('ledger_name', f'Unknown_{le_idx+1}'),
                            amount=le_amount,
                            is_debit=le.get('is_debit', False),
                            is_credit=le.get('is_credit', False),
                            raw_data=le.get('all_fields', le.get('raw_data', {}))
                        )
                    created += 1
                except Exception as e:
                    logger.error(f"Error saving transaction at idx {idx}: {e}")
                    skipped += 1
                    errors.append({'idx': idx, 'reason': str(e)})
        return Response({
            'message': 'Transactions processed successfully',
            'transactions_created': created,
            'transactions_skipped': skipped,
            'errors': errors[:10]  # Only show first 10 errors for brevity
        }, status=201)
