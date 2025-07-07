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

# Logging setup
LOG_FILE = os.path.join(os.path.dirname(__file__), 'sync_log.txt')
def log(msg):
    timestamp = datetime.datetime.now().strftime('%Y-%m-%d %H:%M:%S')
    with open(LOG_FILE, 'a', encoding='utf-8') as f:
        f.write(f"[{timestamp}] {msg}\n")
    print(f"[LOG] {msg}")

load_dotenv()

if getattr(sys, 'frozen', False):
    base_path = getattr(sys, '_MEIPASS', os.path.abspath("."))
else:
    base_path = os.path.abspath(".")

env_path = os.path.join(base_path, 'config.env')
load_dotenv(dotenv_path=env_path)

TALLY_URL = os.getenv("TALLY_URL")
log(f"Loaded TALLY_URL: {TALLY_URL}")


def test_tally_connection():
    """Test if Tally is reachable using a valid XML request (using default Company Info report)."""
    test_request = """
    <ENVELOPE>
        <HEADER>
            <TALLYREQUEST>Export Data</TALLYREQUEST>
        </HEADER>
        <BODY>
            <EXPORTDATA>
                <REQUESTDESC>
                    <REPORTNAME>Day Book</REPORTNAME>
                </REQUESTDESC>
            </EXPORTDATA>
        </BODY>
    </ENVELOPE>
    """
    if not TALLY_URL:
        log("❌ TALLY_URL is not set. Please check your configuration.")
        messagebox.showerror("Tally Error", "TALLY_URL is not set. Please check your configuration.")
        return False
    try:
        log(f"Sending test connection POST to {TALLY_URL}")
        messagebox.showinfo("Please Wait", "Tally is processing your request.\n\nFor large data or slow devices, this may take up to 2 minutes. Please be patient and do not close Tally or this app.")
        response = requests.post(TALLY_URL, data=test_request, timeout=150)
        log(f"Test connection response: status={response.status_code}, text={response.text[:200]}")
        if response.status_code == 200 and "<ENVELOPE>" in response.text:
            return True
        else:
            log(f"❌ Invalid response from Tally: {response.text}")
            return False
    except Exception as e:
        import traceback
        error_details = traceback.format_exc()
        log(f"❌ Connection failed: {e}\n{error_details}")
        print(f"❌ Connection failed: {e}\n{error_details}")
        return False


def clean_invalid_xml_chars(xml_str):
    """
    Remove all invalid XML 1.0 characters and decode HTML entities.
    Replace any invalid character with '-'.
    """
    # XML 1.0 valid chars: tab (\x09), newline (\x0A), carriage return (\x0D), and \x20-\uD7FF, \uE000-\uFFFD, \U00010000-\U0010FFFF
    # Replace anything else with '-'
    cleaned = re.sub(
        r'[^\x09\x0A\x0D\x20-\uD7FF\uE000-\uFFFD\U00010000-\U0010FFFF]',
        '-',
        xml_str
    )
    return html.unescape(cleaned)


def fix_xml_structure(xml_str):
    """Fix malformed XML structure from Tally TDL output."""
    try:
        # First check if it's already well-formed
        try:
            ET.fromstring(xml_str)
            return xml_str
        except ET.ParseError:
            pass
        
        # If not well-formed, try to fix it
        log("XML is not well-formed, attempting to fix...")
        
        # Clean invalid characters first
        xml_str = clean_invalid_xml_chars(xml_str)
        
        # If XML doesn't start with proper declaration, add it
        if not xml_str.strip().startswith('<?xml'):
            xml_str = '<?xml version="1.0" encoding="UTF-8"?>\n' + xml_str
        
        # If missing root element, wrap in one
        if '<TALLYDATAEXPORT>' not in xml_str:
            # Extract voucher and ledger data
            voucher_pattern = r'<VOUCHER>.*?</VOUCHER>'
            ledger_pattern = r'<LEDGER>.*?</LEDGER>'
            
            vouchers = re.findall(voucher_pattern, xml_str, re.DOTALL)
            ledgers = re.findall(ledger_pattern, xml_str, re.DOTALL)
            
            # Construct proper XML
            fixed_xml = '<?xml version="1.0" encoding="UTF-8"?>\n<TALLYDATAEXPORT>\n'
            
            if vouchers:
                fixed_xml += '<VOUCHERS>\n'
                for voucher in vouchers:
                    fixed_xml += voucher + '\n'
                fixed_xml += '</VOUCHERS>\n'
            
            if ledgers:
                fixed_xml += '<LEDGERS>\n'
                for ledger in ledgers:
                    fixed_xml += ledger + '\n'
                fixed_xml += '</LEDGERS>\n'
            
            fixed_xml += '</TALLYDATAEXPORT>'
            
            # Test if the fixed XML is valid
            try:
                ET.fromstring(fixed_xml)
                log("✅ Successfully fixed XML structure")
                return fixed_xml
            except ET.ParseError as e:
                log(f"❌ Still invalid after fix attempt: {e}")
                return None
        
        return xml_str
        
    except Exception as e:
        log(f"❌ Error fixing XML structure: {e}")
        return None


def clean_narration_for_xml(narration):
    """Clean narration field for XML compatibility."""
    if not narration or not isinstance(narration, str):
        return "-"
    
    # XML entity encoding
    narration = narration.replace("&", "&amp;")
    narration = narration.replace("<", "&lt;")
    narration = narration.replace(">", "&gt;")
    narration = narration.replace("\"", "&quot;")
    narration = narration.replace("'", "&apos;")
    
    # Clean other problematic characters
    narration = narration.replace("\n", " ")
    narration = narration.replace("\t", " ")
    narration = re.sub(r'\s+', ' ', narration)  # Multiple spaces to single space
    narration = narration.strip()
    
    if not narration:
        return "-"
    return narration


def postprocess_vouchers(data):
    """Recursively clean all Narration fields in parsed Tally data."""
    if isinstance(data, dict):
        for k, v in data.items():
            if k.upper() == 'NARRATIONFIELDEXPORT':
                data[k] = clean_narration_for_xml(v)
            else:
                postprocess_vouchers(v)
    elif isinstance(data, list):
        for item in data:
            postprocess_vouchers(item)


def xml_to_json(xml_str):
    """Convert Tally XML string to JSON string."""
    try:
        # First try to fix the XML structure
        fixed_xml = fix_xml_structure(xml_str)
        if not fixed_xml:
            return None
            
        parsed_dict = xmltodict.parse(fixed_xml)
        json_data = json.dumps(parsed_dict, indent=2, ensure_ascii=False)
        return json_data
    except Exception as e:
        log(f"❌ Error converting XML to JSON: {e}")
        return None


def clean_field(value):
    """Clean a single string field for XML and data usability."""
    if not isinstance(value, str):
        return value
    # Remove invalid XML chars, replace with '-'
    value = re.sub(r'[^\x09\x0A\x0D\x20-\uD7FF\uE000-\uFFFD\U00010000-\U0010FFFF]', '-', value)
    # Escape XML entities
    value = (value.replace('&', '&amp;')
                  .replace('<', '&lt;')
                  .replace('>', '&gt;')
                  .replace('"', '&quot;')
                  .replace("'", '&apos;'))
    return value.strip() or "-"


def clean_dict_fields(data):
    """Recursively clean all string fields in a dict or list."""
    if isinstance(data, dict):
        return {k: clean_dict_fields(v) for k, v in data.items()}
    elif isinstance(data, list):
        return [clean_dict_fields(item) for item in data]
    elif isinstance(data, str):
        return clean_field(data)
    else:
        return data


def send_tally_request(xml_request: str, return_json: bool = False) -> dict | None:
    """Send XML Request to Tally and return parsed response or JSON if requested."""
    if not TALLY_URL:
        log("❌ TALLY_URL is not set. Please check your configuration.")
        messagebox.showerror("Tally Error", "TALLY_URL is not set. Please check your configuration.")
        return None
    try:
        log(f"Sending data request to {TALLY_URL} with XML: {xml_request[:100]}")
        messagebox.showinfo("Please Wait", "Tally is processing your request.\n\nFor large data or slow devices, this may take up to 2 minutes. Please be patient and do not close Tally or this app.")
        response = requests.post(TALLY_URL, data=xml_request, timeout=120)
        log(f"Data request response: status={response.status_code}, text={response.text[:200]}")
        if response.status_code == 200:
            # Check for Tally errors
            if any(err in response.text for err in ['<LINEERROR>', 'Error in TDL', 'No PARTS', 'No LINES', 'No BUTTONS']):
                log(f"❌ Tally returned error: {response.text}")
                messagebox.showerror("Tally Error", f"Tally returned error. Please check Tally and try again.\n\n{response.text}")
                return None
            # Check for basic XML structure
            if '<ENVELOPE>' not in response.text and '<TALLYDATAEXPORT>' not in response.text:
                log(f"❌ Tally response missing expected XML structure: {response.text}")
                messagebox.showerror("Tally Error", f"Tally did not return valid data.\n\n{response.text}")
                return None
            try:
                if return_json:
                    json_str = xml_to_json(response.text)
                    if json_str is None:
                        return None
                    data = json.loads(json_str)
                    data = clean_dict_fields(data)
                    if not isinstance(data, dict):
                        return {"data": data}
                    return data
                else:
                    fixed_xml = fix_xml_structure(response.text)
                    if not fixed_xml:
                        return None
                    parsed = xmltodict.parse(fixed_xml)
                    postprocess_vouchers(parsed)
                    parsed = clean_dict_fields(parsed)
                    if not isinstance(parsed, dict):
                        return {"data": parsed}
                    return parsed
            except Exception as parse_err:
                error_sample = response.text[:500]
                log(f"❌ Failed to parse Tally XML: {parse_err}\nSnippet: {error_sample}")
                messagebox.showerror("Tally Error", f"Failed to parse Tally XML.\n\n{parse_err}\n\n{error_sample}")
                return None
        else:
            log(f"❌ Tally responded with status: {response.status_code}")
            messagebox.showerror("Tally Error", f"Tally responded with status: {response.status_code}")
            return None
    except requests.exceptions.Timeout:
        log("❌ Timeout while connecting to Tally.")
        messagebox.showerror("Tally Error", "Timeout while connecting to Tally. Please check if Tally is running and accessible.")
        return None
    except Exception as e:
        log(f"❌ Error fetching data from Tally: {e}")
        messagebox.showerror("Tally Error", f"Error fetching data from Tally: {e}")
        return None


def fetch_daybook_data(start_date="20240401", end_date="20250630") -> dict | None:
    """Fetch Daybook using Custom TDL Report."""
    xml_request = f"""
    <ENVELOPE>
        <HEADER>
            <TALLYREQUEST>Export Data</TALLYREQUEST>
        </HEADER>
        <BODY>
            <EXPORTDATA>
                <REQUESTDESC>
                    <REPORTNAME>Export Data XML</REPORTNAME>
                    <STATICVARIABLES>
                        <SVFROMDATE>{start_date}</SVFROMDATE>
                        <SVTODATE>{end_date}</SVTODATE>
                        <EXPLODEFLAG>Yes</EXPLODEFLAG>
                        <SVEXPORTFORMAT>XML</SVEXPORTFORMAT>
                    </STATICVARIABLES>
                </REQUESTDESC>
            </EXPORTDATA>
        </BODY>
    </ENVELOPE>
    """
    return send_tally_request(xml_request)


def fetch_ledger_details(start_date="20240401", end_date="20250630") -> dict | None:
    """Fetch Detailed Ledger Information including opening balances using default report."""
    xml_request = f"""
    <ENVELOPE>
        <HEADER>
            <TALLYREQUEST>Export Data</TALLYREQUEST>
        </HEADER>
        <BODY>
            <EXPORTDATA>
                <REQUESTDESC>
                    <REPORTNAME>Ledger Vouchers</REPORTNAME>
                    <STATICVARIABLES>
                        <SVFROMDATE>{start_date}</SVFROMDATE>
                        <SVTODATE>{end_date}</SVTODATE>
                        <EXPLODEFLAG>Yes</EXPLODEFLAG>
                        <SVEXPORTFORMAT>XML</SVEXPORTFORMAT>
                    </STATICVARIABLES>
                </REQUESTDESC>
            </EXPORTDATA>
        </BODY>
    </ENVELOPE>
    """
    return send_tally_request(xml_request)


def fetch_export_data(start_date="20240401", end_date="20250630") -> dict | None:
    """Fetch Daybook and Ledger data using Export.tdl (Export Data XML report)."""
    xml_request = f"""
    <ENVELOPE>
        <HEADER>
            <TALLYREQUEST>Export Data</TALLYREQUEST>
        </HEADER>
        <BODY>
            <EXPORTDATA>
                <REQUESTDESC>
                    <REPORTNAME>Export Data XML</REPORTNAME>
                    <STATICVARIABLES>
                        <SVFROMDATE>{start_date}</SVFROMDATE>
                        <SVTODATE>{end_date}</SVTODATE>
                        <EXPLODEFLAG>Yes</EXPLODEFLAG>
                        <SVEXPORTFORMAT>XML</SVEXPORTFORMAT>
                    </STATICVARIABLES>
                </REQUESTDESC>
            </EXPORTDATA>
        </BODY>
    </ENVELOPE>
    """
    return send_tally_request(xml_request)


def fetch_export_data_json(start_date="20240401", end_date="20250630") -> dict | None:
    """Fetch Daybook and Ledger data as JSON using Export.tdl (Export Data XML report)."""
    xml_request = f"""
    <ENVELOPE>
        <HEADER>
            <TALLYREQUEST>Export Data</TALLYREQUEST>
        </HEADER>
        <BODY>
            <EXPORTDATA>
                <REQUESTDESC>
                    <REPORTNAME>Export Data XML</REPORTNAME>
                    <STATICVARIABLES>
                        <SVFROMDATE>{start_date}</SVFROMDATE>
                        <SVTODATE>{end_date}</SVTODATE>
                        <EXPLODEFLAG>Yes</EXPLODEFLAG>
                        <SVEXPORTFORMAT>XML</SVEXPORTFORMAT>
                    </STATICVARIABLES>
                </REQUESTDESC>
            </EXPORTDATA>
        </BODY>
    </ENVELOPE>
    """
    return send_tally_request(xml_request, return_json=True)


def fetch_ledger_masters() -> list:
    """Fetch all ledger masters with opening balances, under category, and amount using default report."""
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
                        <ACCOUNTTYPE>Ledger</ACCOUNTTYPE>
                        <SVEXPORTFORMAT>XML</SVEXPORTFORMAT>
                    </STATICVARIABLES>
                </REQUESTDESC>
            </EXPORTDATA>
        </BODY>
    </ENVELOPE>
    """

    raw_data = send_tally_request(xml_request)

    if not raw_data:
        log("❌ Failed to fetch ledger masters from Tally.")
        return []

    try:
        ledgers = []
        accounts = raw_data.get('ENVELOPE', {}).get('BODY', {}).get('DATA', {}).get('TALLYMESSAGE', []) if raw_data else []

        if not isinstance(accounts, list):
            accounts = [accounts]

        for account in accounts:
            ledger = account.get('LEDGER', {}) if account else {}
            name = ledger.get('@NAME', '') if ledger else ''
            under = ledger.get('PARENT', '') if ledger else ''
            opening_balance = ledger.get('OPENINGBALANCE', '0').replace(' Dr', '').replace(' Cr', '').strip() if ledger else '0'

            try:
                opening_balance_value = float(opening_balance)
            except ValueError:
                opening_balance_value = 0

            if opening_balance_value != 0:
                ledgers.append({
                    "name": name,
                    "under": under,
                    "opening_balance": opening_balance_value,
                    "amount": opening_balance_value
                })

        log(f"✅ Extracted {len(ledgers)} ledgers with opening balances.")
        return ledgers

    except Exception as e:
        log(f"❌ Error parsing ledger masters: {e}")
        return []


def get_company_name():
    """Fetch and return the company name from Tally."""
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
                        <SVEXPORTFORMAT>XML</SVEXPORTFORMAT>
                    </STATICVARIABLES>
                </REQUESTDESC>
            </EXPORTDATA>
        </BODY>
    </ENVELOPE>
    """
    data = send_tally_request(xml_request)
    if not data:
        return None
    envelope = data.get('ENVELOPE', {}) if data else {}
    body = envelope.get('BODY', {}) if envelope else {}
    data_section = body.get('DATA', {}) if body else {}
    tally_message = data_section.get('TALLYMESSAGE', {}) if data_section else {}
    company = tally_message.get('COMPANY', {}) if tally_message else {}
    return company.get('@NAME', None) if company else None


def filter_daybook_vouchers(daybook_data):
    """Filter and return only relevant vouchers from daybook data."""
    if not daybook_data:
        return []
    envelope = daybook_data.get('ENVELOPE', {}) if daybook_data else {}
    body = envelope.get('BODY', {}) if envelope else {}
    data_section = body.get('DATA', {}) if body else {}
    tally_message = data_section.get('TALLYMESSAGE', []) if data_section else []
    if not isinstance(tally_message, list):
        tally_message = [tally_message]
    vouchers = []
    for msg in tally_message:
        voucher = msg.get('VOUCHER', None) if msg else None
        if voucher:
            vouchers.append(voucher)
    return vouchers


def fetch_tally_data() -> dict | None:
    """Fetch only Daybook data from Tally for basic connectivity test."""
    log("🔍 Fetching Daybook Data Only (Basic Test)...")
    raw_daybook = fetch_daybook_data()
    if not raw_daybook:
        log("❌ Failed to fetch daybook data from Tally.")
        return None
    log("✅ Fetched daybook data successfully.")
    try:
        vouchers = raw_daybook.get('TALLYDATAEXPORT', {}).get('VOUCHERS', {}).get('VOUCHER', [])
        if not isinstance(vouchers, list):
            vouchers = [vouchers] if vouchers else []
        log(f"Fetched {len(vouchers)} vouchers from daybook.")
    except Exception as e:
        log(f"Could not summarize daybook data: {e}")
    return {"daybook": raw_daybook}




# tally_connector.py as an alternative

def fetch_vouchers_standard_report(start_date="20240401", end_date="20250630"):
    """Fetch vouchers using standard Tally Day Book report."""
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
    return send_tally_request(xml_request)

def fetch_ledgers_standard_report():
    """Fetch ledgers using standard Tally report."""
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
    return send_tally_request(xml_request)

# Update your fetch_export_data function to use standard reports
def fetch_export_data_standard(start_date="20240401", end_date="20250630"):
    """Fetch data using standard Tally reports instead of custom TDL."""
    log("🔍 Fetching data using standard Tally reports...")
    
    # Get vouchers
    vouchers = fetch_vouchers_standard_report(start_date, end_date)
    if not vouchers:
        log("❌ Failed to fetch vouchers")
        return None
    
    # Get ledgers
    ledgers = fetch_ledgers_standard_report()
    if not ledgers:
        log("❌ Failed to fetch ledgers")
        return None
    
    log("✅ Successfully fetched data using standard reports")
    return {
        "vouchers": vouchers,
        "ledgers": ledgers
    }