from django.shortcuts import render
from rest_framework import status
from rest_framework.decorators import api_view, permission_classes
from rest_framework.permissions import AllowAny
from rest_framework.response import Response
from django.db import transaction
from .models import Client, TallyTransaction
import json
from datetime import datetime
from django.db import models  # type: ignore

# Create your views here.

@api_view(['POST'])
@permission_classes([AllowAny])
def receive_tally_transactions(request):
    """
    Receive Tally transactions from the sync agent and store them grouped by client
    """
    try:
        data = request.data
        
        if not isinstance(data, list):
            return Response(
                {'error': 'Data must be a list of transactions'}, 
                status=status.HTTP_400_BAD_REQUEST
            )
        
        transactions_created = 0
        clients_created = 0
        
        with transaction.atomic():  # type: ignore
            for transaction_data in data:
                # Extract party name (client name from Tally)
                party_name = transaction_data.get('party_name', '').strip()
                if not party_name:
                    continue
                
                # Get or create client based on party name
                client, created = Client.objects.get_or_create(  # type: ignore
                    name=party_name,
                    defaults={'address': ''}
                )
                if created:
                    clients_created += 1
                
                # Parse date
                date_str = transaction_data.get('date', '')
                try:
                    if date_str:
                        # Handle different date formats
                        if '/' in date_str:
                            date_obj = datetime.strptime(date_str, '%d/%m/%Y').date()
                        else:
                            date_obj = datetime.strptime(date_str, '%Y-%m-%d').date()
                    else:
                        date_obj = datetime.now().date()
                except ValueError:
                    date_obj = datetime.now().date()
                
                # Create transaction record
                TallyTransaction.objects.create(  # type: ignore
                    voucher_no=transaction_data.get('voucher_no', ''),
                    date=date_obj,
                    party_name=party_name,
                    narration=transaction_data.get('narration', ''),
                    amount=transaction_data.get('amount', 0.0),
                    register_type=transaction_data.get('register_type', 'journal'),
                    client=client
                )
                transactions_created += 1
        
        return Response({
            'message': 'Transactions processed successfully',
            'transactions_created': transactions_created,
            'clients_created': clients_created
        }, status=status.HTTP_201_CREATED)
        
    except Exception as e:
        return Response(
            {'error': f'Error processing transactions: {str(e)}'}, 
            status=status.HTTP_500_INTERNAL_SERVER_ERROR
        )

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
