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

try:
    from tenacity import retry, stop_after_attempt, wait_exponential, retry_if_exception_type
except ImportError:
    from tkinter import Tk, messagebox
    root = Tk()
    root.withdraw()
    messagebox.showerror(
        "Missing Dependency",
        "The required package 'tenacity' is not installed.\n"
        "Please install it using 'pip install tenacity' and restart the application."
    )
    raise

import re
import html
from dateutil import parser, rrule
from datetime import timedelta

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
READ_TIMEOUT = 120

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
    
    test_request = """
    <ENVELOPE>
        <HEADER>
            <TALLYREQUEST>Export Data</TALLYREQUEST>
        </HEADER>
        <BODY>
            <EXPORTDATA>
                <REQUESTDESC>
                    <REPORTNAME>Ledger</REPORTNAME>
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
    """Clean and fix XML data for proper parsing."""
    if not xml_str:
        return ""
    
    # Remove invalid XML characters
    cleaned = re.sub(r'[^\x09\x0A\x0D\x20-\uD7FF\uE000-\uFFFD\U00010000-\U0010FFFF]', '', xml_str)
    
    # Unescape HTML entities
    cleaned = html.unescape(cleaned)
    
    # Fix ampersands that are not part of entities
    cleaned = re.sub(r'&(?!amp;|lt;|gt;|apos;|quot;)', '&amp;', cleaned)
    
    # Remove control characters
    cleaned = re.sub(r'[\x00-\x08\x0B\x0C\x0E-\x1F]', '', cleaned)
    
    # Ensure XML declaration exists
    if not cleaned.strip().startswith('<?xml'):
        cleaned = '<?xml version="1.0" encoding="UTF-8"?>\n' + cleaned
    
    return cleaned

@retry(
    stop=stop_after_attempt(MAX_RETRIES),
    wait=wait_exponential(multiplier=1, min=RETRY_DELAY, max=10),
    retry=retry_if_exception_type((requests.exceptions.ConnectionError, requests.exceptions.Timeout))
)
def send_tally_request(xml_request):
    """Send XML request to Tally and return parsed response or recoverable vouchers on XML error."""
    url = os.getenv("TALLY_URL", "http://localhost:9000")
    headers = {'Content-Type': 'application/xml'}
    try:
        response = requests.post(
            url,
            data=xml_request.encode('utf-8'),
            headers=headers,
            timeout=(CONNECTION_TIMEOUT, READ_TIMEOUT)
        )
        if response.status_code == 200:
            # Save raw response for debugging
            with open("raw_tally_response.xml", "w", encoding="utf-8") as f:
                f.write(response.text)
            # Clean and parse XML
            cleaned_xml = clean_xml_data(response.text)
            try:
                return xmltodict.parse(cleaned_xml)
            except Exception as e:
                log(f"❌ XML Parse error: {e}")
                log(f"Raw response: {response.text[:500]}...")
                # --- Enhanced recovery: extract <VOUCHER> blocks ---
                voucher_blocks = re.findall(r'<VOUCHER[\s\S]*?</VOUCHER>', response.text)
                recovered = 0
                skipped = 0
                vouchers = []
                for vb in voucher_blocks:
                    try:
                        # Wrap in root for parsing
                        xml_fragment = f'<?xml version="1.0" encoding="UTF-8"?><ENVELOPE>{vb}</ENVELOPE>'
                        d = xmltodict.parse(xml_fragment)
                        # Extract voucher dict
                        v = d.get('ENVELOPE', {}).get('VOUCHER')
                        if v:
                            vouchers.append(v)
                            recovered += 1
                        else:
                            skipped += 1
                    except Exception as ve:
                        skipped += 1
                log(f"[RECOVERY] Extracted {recovered} vouchers from malformed XML, skipped {skipped}.")
                # Save failed chunk for manual review
                with open("failed_chunk_raw.xml", "w", encoding="utf-8") as f:
                    f.write(response.text)
                # Return as if it was a normal response
                return {'ENVELOPE': {'VOUCHER': vouchers}}
        else:
            log(f"❌ HTTP error: {response.status_code}")
            log(f"Response: {response.text[:200]}...")
            return None
    except Exception as e:
        log(f"❌ Request error: {e}")
        raise

def get_company_name():
    """Get the currently open company name from Tally using Company Info or fallback to custom TDL."""
    # 1. Try built-in Company Info report
    xml_request = """
    <ENVELOPE>
        <HEADER>
            <TALLYREQUEST>Export Data</TALLYREQUEST>
        </HEADER>
        <BODY>
            <EXPORTDATA>
                <REQUESTDESC>
                    <REPORTNAME>List of Companies</REPORTNAME>
                </REQUESTDESC>
            </EXPORTDATA>
        </BODY>
    </ENVELOPE>
    """
    data = send_tally_request(xml_request)
    if data:
        try:
            # ENVELOPE > BODY > DATA > TALLYMESSAGE > COMPANY > NAME
            companies = data.get('ENVELOPE', {}).get('BODY', {}).get('DATA', {}).get('TALLYMESSAGE', [])
            if isinstance(companies, dict):
                companies = [companies]
            for company in companies:
                comp = company.get('COMPANY')
                if comp:
                    name = comp.get('NAME')
                    if name:
                        log(f"✅ Extracted company name: {name}")
                        return name
        except Exception as e:
            log(f"❌ Error extracting company name from Company Info: {e}")

    # 2. Fallback: Try your custom TDL report
    xml_request = """
    <ENVELOPE>
        <HEADER>
            <TALLYREQUEST>Export Data</TALLYREQUEST>
        </HEADER>
        <BODY>
            <EXPORTDATA>
                <REQUESTDESC>
                    <REPORTNAME>Export Company Name XML</REPORTNAME>
                </REQUESTDESC>
            </EXPORTDATA>
        </BODY>
    </ENVELOPE>
    """
    data = send_tally_request(xml_request)
    if data:
        try:
            msg = data.get('ENVELOPE', {}).get('BODY', {}).get('DATA', {}).get('TALLYMESSAGE', {})
            if msg:
                if isinstance(msg, dict):
                    for v in msg.values():
                        if isinstance(v, str) and v.strip():
                            log(f"✅ Extracted company name from custom TDL: {v.strip()}")
                            return v.strip()
                elif isinstance(msg, list):
                    for m in msg:
                        for v in m.values():
                            if isinstance(v, str) and v.strip():
                                log(f"✅ Extracted company name from custom TDL: {v.strip()}")
                                return v.strip()
        except Exception as e:
            log(f"❌ Error extracting company name from custom TDL: {e}")

    log("❌ Could not extract company name from Tally")
    return None

def extract_vouchers_from_response(response_data):
    """Extract vouchers from any nested structure in Tally response."""
    vouchers = []
    
    def traverse_and_extract(obj):
        if isinstance(obj, dict):
            # Check if this object contains vouchers
            if 'VOUCHER' in obj:
                voucher_data = obj['VOUCHER']
                if isinstance(voucher_data, list):
                    vouchers.extend(voucher_data)
                else:
                    vouchers.append(voucher_data)
            
            # Recursively check all values
            for key, value in obj.items():
                if isinstance(value, (dict, list)):
                    traverse_and_extract(value)
        elif isinstance(obj, list):
            for item in obj:
                traverse_and_extract(item)
    
    traverse_and_extract(response_data)
    return vouchers

def fetch_all_vouchers_by_daybook(start_date, end_date):
    """Fetch ALL vouchers using Day Book method - most reliable for getting complete data."""
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
    
    log(f"Fetching all vouchers from Day Book: {start_date} to {end_date}")
    result = send_tally_request(xml_request)
    
    if not result:
        log("❌ No response from Tally Day Book")
        return []
    
    # Extract all vouchers from the response
    all_vouchers = extract_vouchers_from_response(result)
    
    # Log voucher types found
    voucher_types = {}
    for voucher in all_vouchers:
        if isinstance(voucher, dict):
            vtype = voucher.get('VOUCHERTYPENAME', 'Unknown').strip()
            voucher_types[vtype] = voucher_types.get(vtype, 0) + 1
    
    log(f"✅ Day Book extracted {len(all_vouchers)} vouchers")
    log(f"Voucher types found: {voucher_types}")
    
    return all_vouchers

def fetch_vouchers_by_type(report_name, start_date, end_date):
    """
    Fetch vouchers of a specific type using the correct Tally report name (e.g., 'Sales Vouchers').
    Returns a list of voucher dicts.
    """
    xml_request = f"""
    <ENVELOPE>
        <HEADER>
            <TALLYREQUEST>Export Data</TALLYREQUEST>
        </HEADER>
        <BODY>
            <EXPORTDATA>
                <REQUESTDESC>
                    <REPORTNAME>{report_name}</REPORTNAME>
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
    log(f"Fetching vouchers from report '{report_name}' for {start_date} to {end_date}")
    result = send_tally_request(xml_request)
    if not result:
        log(f"❌ No response from Tally for {report_name}")
        return []
    vouchers = extract_vouchers_from_response(result)
    log(f"✅ Extracted {len(vouchers)} vouchers from {report_name}")
    return vouchers

def fetch_vouchers_by_type_chunked(report_name, start_date, end_date, chunk_days=30):
    """
    Fetch vouchers of a specific type in chunks to avoid Tally timeouts.
    Returns a list of voucher dicts.
    """
    start = parser.parse(start_date)
    end = parser.parse(end_date)
    all_vouchers = []
    chunk_count = 0
    while start <= end:
        chunk_start = start
        chunk_end = min(start + timedelta(days=chunk_days-1), end)
        chunk_start_str = chunk_start.strftime('%Y%m%d')
        chunk_end_str = chunk_end.strftime('%Y%m%d')
        log(f"Fetching {report_name} chunk: {chunk_start_str} to {chunk_end_str}")
        vouchers = fetch_vouchers_by_type(report_name, chunk_start_str, chunk_end_str)
        all_vouchers.extend(vouchers)
        log(f"Chunk {chunk_start_str}-{chunk_end_str}: {len(vouchers)} vouchers")
        start = chunk_end + timedelta(days=1)
        chunk_count += 1
    log(f"✅ Total {report_name} vouchers fetched in chunks: {len(all_vouchers)}")
    return all_vouchers

def fetch_all_7_voucher_types(start_date, end_date, chunk_days=30):
    """
    Fetch all 7 accounting voucher types using the correct report names, in chunks.
    Returns a list of all vouchers (dicts) for the date range.
    """
    report_map = [
        ("Sales Vouchers", "Sales"),
        ("Purchase Vouchers", "Purchase"),
        ("Payment Vouchers", "Payment"),
        ("Receipt Vouchers", "Receipt"),
        ("Journal Vouchers", "Journal"),
        ("Credit Note Vouchers", "Credit Note"),
        ("Debit Note Vouchers", "Debit Note"),
    ]
    all_vouchers = []
    type_counts = {}
    for report_name, vtype in report_map:
        vouchers = fetch_vouchers_by_type_chunked(report_name, start_date, end_date, chunk_days=chunk_days)
        for voucher in vouchers:
            if isinstance(voucher, dict):
                voucher_type = voucher.get('VOUCHERTYPENAME', '').strip()
                type_counts[voucher_type] = type_counts.get(voucher_type, 0) + 1
                all_vouchers.append(voucher)
        log(f"{report_name}: {len(vouchers)} vouchers fetched.")
    log(f"✅ Total vouchers extracted: {len(all_vouchers)} by type: {type_counts}")
    return all_vouchers

def fetch_accounting_vouchers_only(start_date, end_date, chunk_days=30):
    """
    Fetch only the 7 accounting voucher types using the correct report names, in chunks.
    Returns a list of voucher dicts.
    """
    return fetch_all_7_voucher_types(start_date, end_date, chunk_days=chunk_days)

def fetch_ledger_opening_balances():
    """Fetch opening balances for all ledgers."""
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
    
    log("Fetching ledger opening balances")
    result = send_tally_request(xml_request)
    
    if not result:
        log("❌ No response from Tally for ledger opening balances")
        return []
    
    opening_balances = []
    
    def extract_ledger_info(obj):
        if isinstance(obj, dict):
            # Look for LEDGER objects
            if 'LEDGER' in obj:
                ledger_data = obj['LEDGER']
                if isinstance(ledger_data, list):
                    for ledger in ledger_data:
                        process_ledger(ledger)
                else:
                    process_ledger(ledger_data)
            
            # Recursively search
            for key, value in obj.items():
                if isinstance(value, (dict, list)):
                    extract_ledger_info(value)
        elif isinstance(obj, list):
            for item in obj:
                extract_ledger_info(item)
    
    def process_ledger(ledger):
        if isinstance(ledger, dict):
            ledger_name = ledger.get('NAME', '').strip()
            opening_balance = ledger.get('OPENINGBALANCE', '0')
            ledger_group = ledger.get('PARENT', '').strip()
            
            # Clean opening balance value
            if isinstance(opening_balance, str):
                # Remove currency symbols and clean the value
                cleaned_balance = re.sub(r'[^\d.-]', '', opening_balance)
                try:
                    balance_value = float(cleaned_balance) if cleaned_balance else 0.0
                except:
                    balance_value = 0.0
            else:
                balance_value = float(opening_balance) if opening_balance else 0.0
            
            if ledger_name and balance_value != 0:
                opening_balances.append({
                    'ledger_name': ledger_name,
                    'opening_balance': balance_value,
                    'group': ledger_group,
                    'raw_balance': opening_balance
                })
    
    extract_ledger_info(result)
    
    log(f"✅ Extracted {len(opening_balances)} ledger opening balances")
    
    # Save to file for debugging
    with open("opening_balances.json", "w", encoding="utf-8") as f:
        json.dump(opening_balances, f, indent=2, ensure_ascii=False)
    
    return opening_balances

def fetch_complete_tally_data(start_date, end_date):
    """Fetch complete Tally data: vouchers + opening balances."""
    log(f"🔍 Fetching complete Tally data from {start_date} to {end_date}")
    try:
        # Fetch accounting vouchers (7 types)
        accounting_vouchers = fetch_accounting_vouchers_only(start_date, end_date)
        # Fetch opening balances
        opening_balances = fetch_ledger_opening_balances()
        # Prepare complete data structure (company_name only for local use, not for backend)
        complete_data = {
            "company_name": get_company_name(),  # For local/logging only
            "date_range": {
                "from_date": start_date,
                "to_date": end_date
            },
            "export_info": {
                "exported_at": datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
                "total_vouchers": len(accounting_vouchers),
                "total_opening_balances": len(opening_balances)
            },
            "accounting_vouchers": accounting_vouchers,
            "opening_balances": opening_balances
        }
        # Save complete data to file
        with open("complete_tally_data.json", "w", encoding="utf-8") as f:
            json.dump(complete_data, f, indent=2, ensure_ascii=False)
        log(f"✅ Complete data export finished:")
        log(f"   - Vouchers: {len(accounting_vouchers)}")
        log(f"   - Opening Balances: {len(opening_balances)}")
        return complete_data
    except Exception as e:
        log(f"❌ Error fetching complete Tally data: {e}")
        return None

def fetch_7_voucher_types_json(start_date, end_date):
    """Fetch 7 accounting voucher types and return as JSON."""
    complete_data = fetch_complete_tally_data(start_date, end_date)
    
    if complete_data:
        return json.dumps(complete_data, indent=2, ensure_ascii=False)
    else:
        return json.dumps({
            "error": "Failed to fetch data from Tally",
            "company_name": get_company_name() or "Unknown",
            "date_range": {"from_date": start_date, "to_date": end_date},
            "accounting_vouchers": [],
            "opening_balances": []
        }, indent=2, ensure_ascii=False)

# Legacy compatibility functions
def fetch_vouchers(start_date, end_date):
    """Legacy function - fetch vouchers using Day Book."""
    return fetch_all_vouchers_by_daybook(start_date, end_date)

def fetch_export_data_json(start_date, end_date, chunk_days=1):
    """Legacy function - fetch complete data as JSON."""
    return fetch_7_voucher_types_json(start_date, end_date)

def fetch_export_data(start_date, end_date):
    """Legacy function - fetch data as dict."""
    json_data = fetch_export_data_json(start_date, end_date)
    if json_data:
        try:
            return json.loads(json_data)
        except:
            return None
    return None

def extract_ledger_entries_from_voucher(voucher):
    """
    Extract all credit/debit ledger entries from a voucher dict.
    Returns a list of dicts: [{ledger_name, amount, is_debit, is_credit, ...}]
    """
    entries = []
    # Tally can use ALLLEDGERENTRIES.LIST or LEDGERENTRIES.LIST
    ledger_lists = []
    for key in ["ALLLEDGERENTRIES.LIST", "LEDGERENTRIES.LIST"]:
        if key in voucher:
            val = voucher[key]
            if isinstance(val, list):
                ledger_lists.extend(val)
            elif isinstance(val, dict):
                ledger_lists.append(val)
    for entry in ledger_lists:
        if not isinstance(entry, dict):
            continue
        ledger_name = entry.get("LEDGERNAME", "").strip()
        amount = entry.get("AMOUNT", "0")
        # Tally: Debit is positive, Credit is negative (usually)
        try:
            amt_val = float(str(amount).replace(",", ""))
        except:
            amt_val = 0.0
        is_debit = amt_val > 0
        is_credit = amt_val < 0
        entries.append({
            "ledger_name": ledger_name,
            "amount": amt_val,
            "is_debit": is_debit,
            "is_credit": is_credit,
            "raw_amount": amount,
            "all_fields": entry
        })
    return entries

def fetch_all_registers(start_date, end_date):
    """Enhanced function to fetch all 7 accounting voucher types, including all ledger entries."""
    accounting_vouchers = fetch_accounting_vouchers_only(start_date, end_date)
    transactions = []
    required_fields = ["party_name", "voucher_no", "voucher_type", "date", "amount", "ledger_entries"]
    for voucher in accounting_vouchers:
        if isinstance(voucher, dict):
            vtype = voucher.get('VOUCHERTYPENAME', '').strip()
            voucher_number = voucher.get('VOUCHERNUMBER', '')
            narration = voucher.get('NARRATION', '')
            date = voucher.get('DATE', '')
            # Extract all ledger entries (credit/debit splits)
            ledger_entries = extract_ledger_entries_from_voucher(voucher)
            # --- Ensure all required fields are present ---
            txn = {
                'voucher_type': vtype,
                'voucher_no': voucher_number,
                'date': date,
                'amount': voucher.get('AMOUNT', ''),
                'party_name': voucher.get('PARTYNAME', ''),
                'ledger_entries': ledger_entries,
                'narration': narration,
                'voucher_all_fields': voucher
            }
            # Fill missing required fields with empty values
            for field in required_fields:
                if field not in txn:
                    txn[field] = '' if field != 'ledger_entries' else []
            transactions.append(txn)
    return transactions

# Recovery: also provide a function to convert recovered vouchers to transaction list

def recover_failed_chunk_transactions(xml_path="failed_chunk_raw.xml"):
    """Convert recovered vouchers from failed chunk XML into transaction dicts with all ledger entries."""
    vouchers = recover_failed_chunk_vouchers(xml_path)
    transactions = []
    for voucher in vouchers:
        if isinstance(voucher, dict):
            vtype = voucher.get('VOUCHERTYPENAME', '').strip()
            voucher_number = voucher.get('VOUCHERNUMBER', '')
            narration = voucher.get('NARRATION', '')
            date = voucher.get('DATE', '')
            ledger_entries = extract_ledger_entries_from_voucher(voucher)
            for entry in ledger_entries:
                txn = {
                    'voucher_type': vtype,
                    'register_type': vtype.lower().replace(' ', '_'),
                    'voucher_number': voucher_number,
                    'narration': narration,
                    'date': date,
                    'ledger_name': entry['ledger_name'],
                    'amount': entry['amount'],
                    'is_debit': entry['is_debit'],
                    'is_credit': entry['is_credit'],
                    'raw_amount': entry['raw_amount'],
                    'ledger_entry': entry['all_fields'],
                    'voucher_all_fields': voucher
                }
                transactions.append(txn)
    return transactions

def recover_failed_chunk_vouchers(xml_path="failed_chunk_raw.xml"):
    """
    Extract all <VOUCHER> blocks from a failed chunk XML file, parse each individually, and return as list of dicts.
    Handles malformed XML by extracting blocks with regex.
    """
    vouchers = []
    try:
        with open(xml_path, 'r', encoding='utf-8') as f:
            raw_xml = f.read()
    except Exception as e:
        print(f"Failed to read {xml_path}: {e}")
        return []
    # Use regex to extract all <VOUCHER>...</VOUCHER> blocks
    voucher_blocks = re.findall(r'<VOUCHER[\s\S]*?</VOUCHER>', raw_xml, re.IGNORECASE)
    for block in voucher_blocks:
        try:
            # Wrap in a root for parsing
            xml_str = f'<ROOT>{block}</ROOT>'
            root = ET.fromstring(xml_str)
            voucher_elem = root.find('VOUCHER')
            if voucher_elem is not None:
                voucher_dict = {child.tag: child.text for child in voucher_elem}
                # Also include sub-elements as dicts
                for child in voucher_elem:
                    if list(child):
                        voucher_dict[child.tag] = [
                            {gchild.tag: gchild.text for gchild in subchild}
                            if list(subchild) else subchild.text
                            for subchild in child
                        ]
                vouchers.append(voucher_dict)
        except Exception as e:
            # Log and skip malformed block
            print(f"Failed to parse voucher block: {e}")
            continue
    return vouchers

# CLI test runner
if __name__ == "__main__":
    def test_connection():
        print("=" * 60)
        print("TESTING TALLY CONNECTION")
        print("=" * 60)
        return test_tally_connection()

    def test_company():
        print("\n" + "=" * 60)
        print("TESTING COMPANY NAME")
        print("=" * 60)
        company_name = get_company_name()
        if company_name:
            print(f"✅ Company: {company_name}")
            return True
        else:
            print("❌ Could not fetch company name")
            return False

    def test_vouchers():
        print("\n" + "=" * 60)
        print("TESTING VOUCHER EXTRACTION")
        print("=" * 60)
        vouchers = fetch_accounting_vouchers_only("20240401", "20240410")
        if vouchers:
            print(f"✅ Found {len(vouchers)} accounting vouchers")
            return True
        else:
            print("❌ No vouchers found")
            return False

    def test_opening_balances():
        print("\n" + "=" * 60)
        print("TESTING OPENING BALANCES")
        print("=" * 60)
        balances = fetch_ledger_opening_balances()
        if balances:
            print(f"✅ Found {len(balances)} opening balances")
            return True
        else:
            print("❌ No opening balances found")
            return False

    def test_complete_data():
        print("\n" + "=" * 60)
        print("TESTING COMPLETE DATA EXTRACTION")
        print("=" * 60)
        complete_data = fetch_complete_tally_data("20240401", "20240410")
        if complete_data:
            print(f"✅ Complete data extraction successful")
            print(f"   - Vouchers: {len(complete_data.get('accounting_vouchers', []))}")
            print(f"   - Opening Balances: {len(complete_data.get('opening_balances', []))}")
            return True
        else:
            print("❌ Complete data extraction failed")
            return False

    def main():
        print("🚀 ENHANCED TALLY CONNECTOR TESTS")
        print("=" * 60)
        
        tests = [
            ("Connection Test", test_connection),
            ("Company Name", test_company),
            ("Voucher Extraction", test_vouchers),
            ("Opening Balances", test_opening_balances),
            ("Complete Data", test_complete_data)
        ]
        
        results = {}
        for test_name, test_func in tests:
            try:
                results[test_name] = test_func()
            except Exception as e:
                print(f"❌ {test_name} failed: {e}")
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
        
        return passed == total

    success = main()
    sys.exit(0 if success else 1)




