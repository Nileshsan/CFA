#!/usr/bin/env python3
"""
Test script for Enhanced Tally Connector
Demonstrates extraction of client transaction data for CFA AI system
"""

import sys
import os
import json
from datetime import datetime, timedelta

# Add current directory to path for imports
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

try:
    from tally_connector_1 import (
        test_enhanced_connector,
        fetch_comprehensive_client_data,
        fetch_client_ledgers,
        fetch_specific_client_ledger,
        export_client_data_to_json,
        get_company_name
    )
except ImportError as e:
    print(f"❌ Import error: {e}")
    print("Make sure tally_connector.py is in the same directory")
    sys.exit(1)

def test_basic_functionality():
    """Test basic connector functionality"""
    print("=" * 60)
    print("TESTING BASIC FUNCTIONALITY")
    print("=" * 60)
    
    # Test enhanced connector
    success = test_enhanced_connector()
    
    if success:
        print("✅ Basic functionality test passed")
        return True
    else:
        print("❌ Basic functionality test failed")
        return False

def test_client_ledger_extraction():
    """Test extraction of client ledgers"""
    print("\n" + "=" * 60)
    print("TESTING CLIENT LEDGER EXTRACTION")
    print("=" * 60)
    
    try:
        # Fetch client ledgers
        client_ledgers = fetch_client_ledgers()
        
        if client_ledgers:
            print(f"✅ Found {len(client_ledgers)} client ledgers:")
            for i, ledger in enumerate(client_ledgers[:5], 1):  # Show first 5
                print(f"  {i}. {ledger['name']} ({ledger['parent']})")
                print(f"     Opening: {ledger['opening_balance']} {ledger['opening_balance_type']}")
                print(f"     Closing: {ledger['closing_balance']} {ledger['closing_balance_type']}")
            
            if len(client_ledgers) > 5:
                print(f"  ... and {len(client_ledgers) - 5} more")
            
            return True
        else:
            print("❌ No client ledgers found")
            return False
            
    except Exception as e:
        print(f"❌ Error testing client ledger extraction: {e}")
        return False

def test_specific_client_extraction():
    """Test extraction of specific client data"""
    print("\n" + "=" * 60)
    print("TESTING SPECIFIC CLIENT EXTRACTION")
    print("=" * 60)
    
    try:
        # Get company name first
        company_name = get_company_name()
        if not company_name:
            print("❌ Could not get company name")
            return False
        
        # Get client ledgers to find a test client
        client_ledgers = fetch_client_ledgers()
        if not client_ledgers:
            print("❌ No client ledgers available for testing")
            return False
        
        # Test with first client
        test_client = client_ledgers[0]['name']
        print(f"Testing with client: {test_client}")
        
        # Calculate date range (last 3 months)
        end_date = datetime.now()
        start_date = end_date - timedelta(days=90)
        
        start_date_str = start_date.strftime("%Y%m%d")
        end_date_str = end_date.strftime("%Y%m%d")
        
        # Fetch specific client data
        client_data = fetch_specific_client_ledger(test_client)
        
        if client_data:
            print(f"✅ Successfully extracted data for {test_client}")
            print(f"   Opening Balance: {client_data['opening_balance']} {client_data['opening_balance_type']}")
            print(f"   Closing Balance: {client_data['closing_balance']} {client_data['closing_balance_type']}")
            print(f"   Transactions: {len(client_data['transactions'])}")
            
            # Show sample transaction
            if client_data['transactions']:
                sample_txn = client_data['transactions'][0]
                print(f"   Sample Transaction:")
                print(f"     Date: {sample_txn['date']}")
                print(f"     Type: {sample_txn['voucher_type']}")
                print(f"     Amount: {sample_txn['amount']}")
                print(f"     Balance: {sample_txn['balance']} {sample_txn['balance_type']}")
            
            return True
        else:
            print(f"❌ Could not extract data for {test_client}")
            return False
            
    except Exception as e:
        print(f"❌ Error testing specific client extraction: {e}")
        return False

def test_comprehensive_data_extraction():
    """Test comprehensive data extraction"""
    print("\n" + "=" * 60)
    print("TESTING COMPREHENSIVE DATA EXTRACTION")
    print("=" * 60)
    
    try:
        # Calculate date range (last month)
        end_date = datetime.now()
        start_date = end_date - timedelta(days=30)
        
        start_date_str = start_date.strftime("%Y%m%d")
        end_date_str = end_date.strftime("%Y%m%d")
        
        print(f"Extracting data from {start_date_str} to {end_date_str}")
        
        # Fetch comprehensive data
        comprehensive_data = fetch_comprehensive_client_data()
        
        if comprehensive_data:
            print(f"✅ Successfully extracted comprehensive data")
            print(f"   Company: {comprehensive_data['company_name']}")
            print(f"   Export Date: {comprehensive_data['export_date']}")
            print(f"   Export Time: {comprehensive_data['export_time']}")
            print(f"   Date Range: {comprehensive_data['date_range']['from_date']} to {comprehensive_data['date_range']['to_date']}")
            print(f"   Clients: {len(comprehensive_data['clients'])}")
            
            # Show sample client data
            if comprehensive_data['clients']:
                sample_client = comprehensive_data['clients'][0]
                client_name = sample_client['ledger_info']['name']
                transactions = sample_client['detailed_ledger']['transactions']
                
                print(f"\n   Sample Client: {client_name}")
                print(f"     Opening Balance: {sample_client['ledger_info']['opening_balance']} {sample_client['ledger_info']['opening_balance_type']}")
                print(f"     Closing Balance: {sample_client['ledger_info']['closing_balance']} {sample_client['ledger_info']['closing_balance_type']}")
                print(f"     Transactions: {len(transactions)}")
            
            # Export to JSON
            export_filename = export_client_data_to_json(comprehensive_data)
            if export_filename:
                print(f"   Data exported to: {export_filename}")
            
            return True
        else:
            print("❌ Could not extract comprehensive data")
            return False
            
    except Exception as e:
        print(f"❌ Error testing comprehensive data extraction: {e}")
        return False

def test_data_structure_validation():
    """Validate the structure of extracted data"""
    print("\n" + "=" * 60)
    print("TESTING DATA STRUCTURE VALIDATION")
    print("=" * 60)
    
    try:
        # Get sample data
        end_date = datetime.now()
        start_date = end_date - timedelta(days=7)  # Last week
        
        start_date_str = start_date.strftime("%Y%m%d")
        end_date_str = end_date.strftime("%Y%m%d")
        
        data = fetch_comprehensive_client_data()
        
        if not data:
            print("❌ No data available for validation")
            return False
        
        # Validate structure
        required_fields = [
            'company_name', 'export_date', 'export_time', 
            'date_range', 'clients'
        ]
        
        for field in required_fields:
            if field not in data:
                print(f"❌ Missing required field: {field}")
                return False
        
        print("✅ Basic structure validation passed")
        
        # Validate client structure
        if data['clients']:
            sample_client = data['clients'][0]
            
            required_client_fields = ['ledger_info', 'detailed_ledger']
            for field in required_client_fields:
                if field not in sample_client:
                    print(f"❌ Missing required client field: {field}")
                    return False
            
            # Validate ledger info
            ledger_info = sample_client['ledger_info']
            required_ledger_fields = [
                'name', 'parent', 'opening_balance', 'opening_balance_type',
                'closing_balance', 'closing_balance_type'
            ]
            
            for field in required_ledger_fields:
                if field not in ledger_info:
                    print(f"❌ Missing required ledger field: {field}")
                    return False
            
            # Validate detailed ledger
            detailed_ledger = sample_client['detailed_ledger']
            required_detailed_fields = [
                'client_name', 'opening_balance', 'opening_balance_type',
                'closing_balance', 'closing_balance_type', 'transactions'
            ]
            
            for field in required_detailed_fields:
                if field not in detailed_ledger:
                    print(f"❌ Missing required detailed ledger field: {field}")
                    return False
            
            # Validate transaction structure
            if detailed_ledger['transactions']:
                sample_transaction = detailed_ledger['transactions'][0]
                required_transaction_fields = [
                    'date', 'voucher_type', 'voucher_number', 'amount',
                    'debit_amount', 'credit_amount', 'balance', 'balance_type'
                ]
                
                for field in required_transaction_fields:
                    if field not in sample_transaction:
                        print(f"❌ Missing required transaction field: {field}")
                        return False
            
            print("✅ Client structure validation passed")
            print("✅ Transaction structure validation passed")
        
        return True
        
    except Exception as e:
        print(f"❌ Error in data structure validation: {e}")
        return False

def main():
    """Run all tests"""
    print("🧪 ENHANCED TALLY CONNECTOR TEST SUITE")
    print("Testing CFA client data extraction functionality")
    print("=" * 60)
    
    tests = [
        ("Basic Functionality", test_basic_functionality),
        ("Client Ledger Extraction", test_client_ledger_extraction),
        ("Specific Client Extraction", test_specific_client_extraction),
        ("Comprehensive Data Extraction", test_comprehensive_data_extraction),
        ("Data Structure Validation", test_data_structure_validation)
    ]
    
    passed = 0
    total = len(tests)
    
    for test_name, test_func in tests:
        try:
            if test_func():
                passed += 1
                print(f"✅ {test_name}: PASSED")
            else:
                print(f"❌ {test_name}: FAILED")
        except Exception as e:
            print(f"❌ {test_name}: ERROR - {e}")
    
    print("\n" + "=" * 60)
    print("TEST SUMMARY")
    print("=" * 60)
    print(f"Tests Passed: {passed}/{total}")
    print(f"Success Rate: {(passed/total)*100:.1f}%")
    
    if passed == total:
        print("🎉 All tests passed! Enhanced connector is working correctly.")
    elif passed >= total * 0.8:
        print("⚠️  Most tests passed. Some issues need attention.")
    else:
        print("❌ Multiple tests failed. Please check Tally configuration.")
    
    print("\n" + "=" * 60)
    print("NEXT STEPS")
    print("=" * 60)
    print("1. If all tests passed, the connector is ready for CFA integration")
    print("2. Use fetch_comprehensive_client_data() for production data extraction")
    print("3. Schedule regular data extraction for AI analysis")
    print("4. Monitor logs for any issues")
    print("5. Backup extracted data regularly")

if __name__ == "__main__":
    main() 