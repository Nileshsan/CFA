import requests
import xmltodict
import json
import os
from dotenv import load_dotenv
import sys
import datetime
from tkinter import messagebox
import re
import html
from xml.etree import ElementTree as ET
import time
import socket
import urllib3
from urllib3.exceptions import InsecureRequestWarning
urllib3.disable_warnings(InsecureRequestWarning)

def print_log(msg, level="INFO"):
    """Terminal log printing for CLI feedback"""
    prefix = {
        "INFO": "[LOG]",
        "ERROR": "[ERROR]",
        "WARN": "[WARN]",
        "SUCCESS": "[SUCCESS]"
    }.get(level, "[LOG]")
    print(f"{prefix} {msg}")

# Logging setup
LOG_FILE = os.path.join(os.path.dirname(__file__), 'sync_log.txt')
def log(msg, level="INFO"):
    timestamp = datetime.datetime.now().strftime('%Y-%m-%d %H:%M:%S')
    try:
        with open(LOG_FILE, 'a', encoding='utf-8') as f:
            f.write(f"[{timestamp}] {msg}\n")
    except Exception as e:
        print_log(f"[LOG ERROR] Failed to write to log file: {e}", level="ERROR")
    print_log(msg, level)

load_dotenv()

if getattr(sys, 'frozen', False):
    base_path = getattr(sys, '_MEIPASS', os.path.abspath("."))
else:
    base_path = os.path.abspath(".")

env_path = os.path.join(base_path, 'config.env')
load_dotenv(dotenv_path=env_path)

TALLY_URL = os.getenv("TALLY_URL", "http://localhost:9000")
log(f"Loaded TALLY_URL: {TALLY_URL}")

# Connection configuration
MAX_RETRIES = 3
RETRY_DELAY = 2
CONNECTION_TIMEOUT = 15
READ_TIMEOUT = 60

def check_tally_service():
    """Check if Tally service is running on the specified port."""
    try:
        url_parts = TALLY_URL.replace('http://', '').replace('https://', '')
        host_port = url_parts.split('/')[0]
        host = host_port.split(':')[0]
        port = int(host_port.split(':')[1]) if ':' in host_port else 9000
        
        sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        sock.settimeout(5)
        result = sock.connect_ex((host, port))
        sock.close()
        
        if result == 0:
            log(f"✅ Tally service is running on {host}:{port}")
            return True
        else:
            log(f"❌ Tally service is not running on {host}:{port}")
            return False
    except Exception as e:
        log(f"❌ Error checking Tally service: {e}")
        return False

def create_session():
    """Create a requests session with appropriate settings."""
    session = requests.Session()
    session.headers.update({
        'Content-Type': 'application/xml',
        'User-Agent': 'TallyConnector/1.0',
        'Connection': 'keep-alive'
    })
    return session

def test_tally_connection():
    """Test if Tally is reachable using a simple company info request."""
    if not check_tally_service():
        return False
    
    # Simple test request to get company info
    test_request = """
    <ENVELOPE>
        <HEADER>
            <TALLYREQUEST>Export Data</TALLYREQUEST>
        </HEADER>
        <BODY>
            <EXPORTDATA>
                <REQUESTDESC>
                    <REPORTNAME>List of Accounts</REPORTNAME>
                    <STATICVARIABLES>
                        <ACCOUNTTYPE>Ledger</ACCOUNTTYPE>
                    </STATICVARIABLES>
                </REQUESTDESC>
            </EXPORTDATA>
        </BODY>
    </ENVELOPE>
    """
    
    if not TALLY_URL:
        log("❌ TALLY_URL is not set")
        return False
    
    try:
        log(f"Testing connection to {TALLY_URL}")
        session = create_session()
        response = session.post(
            TALLY_URL, 
            data=test_request.encode('utf-8'),
            timeout=(CONNECTION_TIMEOUT, READ_TIMEOUT)
        )
        
        log(f"Test response: status={response.status_code}, length={len(response.text)}")
        
        if response.status_code == 200 and response.text.strip():
            # Check for valid Tally response patterns
            if any(pattern in response.text for pattern in ['<ENVELOPE>', '<TALLYMESSAGE>', '<COMPANY>', '<NAME>']):
                log("✅ Tally connection test successful")
                return True
            else:
                log(f"❌ Unexpected response format: {response.text[:200]}...")
                return False
        else:
            log(f"❌ HTTP error: {response.status_code}")
            return False
            
    except requests.exceptions.Timeout:
        log("❌ Connection timeout")
        return False
    except requests.exceptions.ConnectionError as e:
        log(f"❌ Connection error: {e}")
        return False
    except Exception as e:
        log(f"❌ Unexpected error: {e}")
        return False
    finally:
        try:
            session.close()
        except:
            pass

def clean_xml_data(xml_str):
    """Clean and fix XML data from Tally."""
    if not xml_str:
        return ""
    
    # Remove invalid XML characters
    cleaned = re.sub(r'[^\x09\x0A\x0D\x20-\uD7FF\uE000-\uFFFD\U00010000-\U0010FFFF]', '', xml_str)
    
    # Decode HTML entities
    cleaned = html.unescape(cleaned)
    
    # Ensure proper XML declaration
    if not cleaned.strip().startswith('<?xml'):
        cleaned = '<?xml version="1.0" encoding="UTF-8"?>\n' + cleaned
    
    return cleaned

def send_tally_request(xml_request, return_json=False, max_retries=MAX_RETRIES):
    """Send XML request to Tally with retry logic."""
    if not TALLY_URL:
        log("❌ TALLY_URL is not set")
        return None
    
    if not check_tally_service():
        log("❌ Tally service is not available")
        return None
    
    last_error = None
    session = create_session()
    
    for attempt in range(max_retries):
        try:
            if attempt > 0:
                log(f"Retry attempt {attempt + 1}/{max_retries}")
                time.sleep(RETRY_DELAY * attempt)
            
            response = session.post(
                TALLY_URL,
                data=xml_request.encode('utf-8'),
                timeout=(CONNECTION_TIMEOUT, READ_TIMEOUT)
            )
            
            if response.status_code == 200 and response.text.strip():
                # Check for Tally error patterns
                error_patterns = [
                    '<LINEERROR>', 'Error in TDL', 'Invalid Report', 
                    'Report not found', 'TDL Error', 'No such report'
                ]
                
                if any(err in response.text for err in error_patterns):
                    log(f"❌ Tally returned error: {response.text[:300]}...")
                    return None
                
                # Clean and parse the response
                cleaned_xml = clean_xml_data(response.text)
                
                try:
                    if return_json:
                        parsed_dict = xmltodict.parse(cleaned_xml)
                        return json.dumps(parsed_dict, indent=2, ensure_ascii=False)
                    else:
                        return xmltodict.parse(cleaned_xml)
                except Exception as parse_err:
                    log(f"❌ Parse error: {parse_err}")
                    last_error = parse_err
                    continue
            else:
                log(f"❌ HTTP error: {response.status_code}")
                last_error = f"HTTP {response.status_code}"
                continue
                
        except requests.exceptions.Timeout:
            log(f"❌ Timeout on attempt {attempt + 1}")
            last_error = "Timeout"
            continue
        except requests.exceptions.ConnectionError as e:
            log(f"❌ Connection error: {e}")
            last_error = f"Connection error: {e}"
            continue
        except Exception as e:
            log(f"❌ Unexpected error: {e}")
            last_error = f"Unexpected error: {e}"
            continue
    
    session.close()
    log(f"❌ All {max_retries} attempts failed. Last error: {last_error}")
    return None

def get_company_name():
    """Get the current company name from Tally."""
    xml_request = """
    <ENVELOPE>
        <HEADER>
            <TALLYREQUEST>Export Data</TALLYREQUEST>
        </HEADER>
        <BODY>
            <EXPORTDATA>
                <REQUESTDESC>
                    <REPORTNAME>List of Accounts</REPORTNAME>
                    <STATICVARIABLES>
                        <ACCOUNTTYPE>Company</ACCOUNTTYPE>
                    </STATICVARIABLES>
                </REQUESTDESC>
            </EXPORTDATA>
        </BODY>
    </ENVELOPE>
    """
    
    data = send_tally_request(xml_request)
    if not data:
        return None
    
    try:
        # Try different paths to find company name
        paths_to_try = [
            ['ENVELOPE', 'BODY', 'DATA', 'TALLYMESSAGE', 'COMPANY', '@NAME'],
            ['ENVELOPE', 'BODY', 'DATA', 'TALLYMESSAGE', 'COMPANY', 'NAME'],
            ['ENVELOPE', 'BODY', 'DATA', 'COMPANY', '@NAME'],
            ['ENVELOPE', 'BODY', 'DATA', 'COMPANY', 'NAME'],
            ['ENVELOPE', 'COMPANY', '@NAME'],
            ['ENVELOPE', 'COMPANY', 'NAME'],
            ['COMPANY', '@NAME'],
            ['COMPANY', 'NAME']
        ]
        
        for path in paths_to_try:
            try:
                current = data
                for key in path:
                    if isinstance(current, dict) and key in current:
                        current = current[key]
                    else:
                        break
                else:
                    if isinstance(current, str) and current.strip():
                        return current.strip()
            except:
                continue
        
        # Fallback: search recursively
        def find_company_name(obj):
            if isinstance(obj, dict):
                for key, value in obj.items():
                    if 'COMPANY' in key.upper() or 'NAME' in key.upper():
                        if isinstance(value, str) and value.strip():
                            return value.strip()
                        elif isinstance(value, dict):
                            result = find_company_name(value)
                            if result:
                                return result
                    else:
                        result = find_company_name(value)
                        if result:
                            return result
            elif isinstance(obj, list):
                for item in obj:
                    result = find_company_name(item)
                    if result:
                        return result
            return None
        
        return find_company_name(data)
        
    except Exception as e:
        log(f"❌ Error extracting company name: {e}")
        return None

def fetch_vouchers(start_date="20240401", end_date="20250630"):
    """Fetch vouchers using Day Book report."""
    xml_request = f"""
    <ENVELOPE>
        <HEADER>
            <TALLYREQUEST>Export Data</TALLYREQUEST>
        </HEADER>
        <BODY>
            <EXPORTDATA>
                <REQUESTDESC>
                    <REPORTNAME>Day Book</REPORTNAME>
                    <STATICVARIABLES>
                        <SVFROMDATE>{start_date}</SVFROMDATE>
                        <SVTODATE>{end_date}</SVTODATE>
                        <EXPLODEFLAG>Yes</EXPLODEFLAG>
                    </STATICVARIABLES>
                </REQUESTDESC>
            </EXPORTDATA>
        </BODY>
    </ENVELOPE>
    """
    
    log(f"Fetching vouchers from {start_date} to {end_date}")
    return send_tally_request(xml_request)

def fetch_ledgers():
    """Fetch ledger master data."""
    xml_request = """
    <ENVELOPE>
        <HEADER>
            <TALLYREQUEST>Export Data</TALLYREQUEST>
        </HEADER>
        <BODY>
            <EXPORTDATA>
                <REQUESTDESC>
                    <REPORTNAME>List of Accounts</REPORTNAME>
                    <STATICVARIABLES>
                        <ACCOUNTTYPE>All Ledgers</ACCOUNTTYPE>
                    </STATICVARIABLES>
                </REQUESTDESC>
            </EXPORTDATA>
        </BODY>
    </ENVELOPE>
    """
    
    log("Fetching ledger master data")
    return send_tally_request(xml_request)

def fetch_groups():
    """Fetch group master data."""
    xml_request = """
    <ENVELOPE>
        <HEADER>
            <TALLYREQUEST>Export Data</TALLYREQUEST>
        </HEADER>
        <BODY>
            <EXPORTDATA>
                <REQUESTDESC>
                    <REPORTNAME>List of Groups</REPORTNAME>
                </REQUESTDESC>
            </EXPORTDATA>
        </BODY>
    </ENVELOPE>
    """
    
    log("Fetching group master data")
    return send_tally_request(xml_request)

def fetch_export_data_json(start_date="20240401", end_date="20250630"):
    """Fetch comprehensive data as JSON without TDL."""
    log(f"🔍 Fetching comprehensive data from {start_date} to {end_date}")
    
    try:
        # Fetch all required data
        company_name = get_company_name()
        vouchers = fetch_vouchers(start_date, end_date)
        ledgers = fetch_ledgers()
        groups = fetch_groups()
        
        # Combine all data
        combined_data = {
            "TALLYDATAEXPORT": {
                "COMPANY": {"NAME": company_name or "Unknown"},
                "REQUESTDATA": {
                    "FROMDATE": start_date,
                    "TODATE": end_date,
                    "EXPORTDATE": datetime.datetime.now().strftime("%Y%m%d"),
                    "EXPORTTIME": datetime.datetime.now().strftime("%H%M%S")
                }
            }
        }
        
        # Add vouchers if available
        if vouchers:
            combined_data["TALLYDATAEXPORT"]["VOUCHERS"] = vouchers
            
        # Add ledgers if available
        if ledgers:
            combined_data["TALLYDATAEXPORT"]["LEDGERS"] = ledgers
            
        # Add groups if available
        if groups:
            combined_data["TALLYDATAEXPORT"]["GROUPS"] = groups
        
        # Convert to JSON
        json_data = json.dumps(combined_data, indent=2, ensure_ascii=False)
        
        log("✅ Successfully fetched and combined data")
        return json_data
        
    except Exception as e:
        log(f"❌ Error fetching export data: {e}")
        return None

# Legacy compatibility functions
def fetch_export_data(start_date="20240401", end_date="20250630"):
    """Legacy function - fetch data as dict."""
    json_data = fetch_export_data_json(start_date, end_date)
    if json_data:
        try:
            return json.loads(json_data)
        except:
            return None
    return None

def fetch_daybook_data(start_date="20240401", end_date="20250630"):
    """Legacy function - fetch vouchers."""
    return fetch_vouchers(start_date, end_date)

def fetch_ledger_details(start_date="20240401", end_date="20250630"):
    """Legacy function - fetch ledgers."""
    return fetch_ledgers()

def fetch_tally_data():
    """Fetch basic Tally data for connectivity test."""
    log("🔍 Fetching basic Tally data...")
    
    try:
        company_name = get_company_name()
        if company_name:
            log(f"✅ Connected to company: {company_name}")
        
        # Get a small sample of data
        sample_vouchers = fetch_vouchers("20240401", "20240410")
        sample_ledgers = fetch_ledgers()
        
        if sample_vouchers or sample_ledgers:
            log("✅ Successfully fetched sample data")
            return {
                "company_name": company_name,
                "sample_vouchers": sample_vouchers,
                "sample_ledgers": sample_ledgers
            }
        else:
            log("❌ No sample data retrieved")
            return None
            
    except Exception as e:
        log(f"❌ Error fetching basic data: {e}")
        return None

# CLI test runner
if __name__ == "__main__":
    def test_basic_connection():
        print("=" * 60)
        print("TESTING BASIC TALLY CONNECTION")
        print("=" * 60)
        return test_tally_connection()

    def test_company_info():
        print("\n" + "=" * 60)
        print("TESTING COMPANY INFO FETCH")
        print("=" * 60)
        company_name = get_company_name()
        if company_name:
            print(f"✅ Company Name: {company_name}")
            return True
        else:
            print("❌ Could not fetch company name")
            return False

    def test_vouchers():
        print("\n" + "=" * 60)
        print("TESTING VOUCHER FETCH")
        print("=" * 60)
        vouchers = fetch_vouchers("20240401", "20240410")
        if vouchers:
            print("✅ Successfully fetched vouchers")
            return True
        else:
            print("❌ Could not fetch vouchers")
            return False

    def test_ledgers():
        print("\n" + "=" * 60)
        print("TESTING LEDGER FETCH")
        print("=" * 60)
        ledgers = fetch_ledgers()
        if ledgers:
            print("✅ Successfully fetched ledgers")
            return True
        else:
            print("❌ Could not fetch ledgers")
            return False

    def test_json_export():
        print("\n" + "=" * 60)
        print("TESTING JSON EXPORT")
        print("=" * 60)
        json_data = fetch_export_data_json("20240401", "20240410")
        if json_data:
            print("✅ Successfully exported data as JSON")
            print(f"JSON size: {len(json_data)} characters")
            return True
        else:
            print("❌ Could not export data as JSON")
            return False

    def main():
        print("🚀 STARTING TALLY CONNECTOR TESTS")
        print("=" * 60)
        
        tests = [
            ("Basic Connection", test_basic_connection),
            ("Company Info", test_company_info),
            ("Voucher Fetch", test_vouchers),
            ("Ledger Fetch", test_ledgers),
            ("JSON Export", test_json_export)
        ]
        
        results = {}
        for test_name, test_func in tests:
            try:
                results[test_name] = test_func()
            except Exception as e:
                print(f"❌ {test_name} failed with exception: {e}")
                results[test_name] = False
        
        print("\n" + "=" * 60)
        print("TEST SUMMARY")
        print("=" * 60)
        
        for test_name, result in results.items():
            status = "✅ PASSED" if result else "❌ FAILED"
            print(f"{test_name:20} : {status}")
        
        passed = sum(1 for result in results.values() if result)
        total = len(results)
        print(f"\nOverall: {passed}/{total} tests passed")
        
        if passed == total:
            print("🎉 All tests passed! Tally connector is working correctly.")
        else:
            print("⚠️  Some tests failed. Check the logs above for details.")
        
        return passed == total

    success = main()
    sys.exit(0 if success else 1)