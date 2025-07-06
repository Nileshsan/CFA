import requests
import xmltodict
import os
from dotenv import load_dotenv
import sys
import datetime
from tkinter import messagebox  # <-- moved to top, always available
import re
import html

# Logging setup
LOG_FILE = os.path.join(os.path.dirname(__file__), 'sync_log.txt')
def log(msg):
    timestamp = datetime.datetime.now().strftime('%Y-%m-%d %H:%M:%S')
    with open(LOG_FILE, 'a', encoding='utf-8') as f:
        f.write(f"[{timestamp}] {msg}\n")
    print(f"[LOG] {msg}")

load_dotenv()

if getattr(sys, 'frozen', False):
    base_path = sys._MEIPASS
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
                    <REPORTNAME>List of Accounts</REPORTNAME>
                </REQUESTDESC>
            </EXPORTDATA>
        </BODY>
    </ENVELOPE>
    """
    try:
        log(f"Sending test connection POST to {TALLY_URL}")
        messagebox.showinfo("Please Wait", "Tally is processing your request.\n\nFor large data or slow devices, this may take up to 2 minutes. Please be patient and do not close Tally or this app.")
        response = requests.post(TALLY_URL, data=test_request, timeout=150)  # 2 minutes
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
    # Remove invalid XML 1.0 characters and decode HTML entities
    cleaned = re.sub(r'[^\x09\x0A\x0D\x20-\uD7FF\uE000-\uFFFD]', ' ', xml_str)
    return html.unescape(cleaned)


def clean_narration_for_xml(narration):
    if not narration or not isinstance(narration, str):
        return "-"
    narration = narration.replace("&", " ")
    narration = narration.replace("<", " ")
    narration = narration.replace(">", " ")
    narration = narration.replace("\"", " ")
    narration = narration.replace("'", " ")
    narration = narration.replace(",", " ")
    narration = narration.replace("\n", " ")
    narration = narration.replace("\t", " ")
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


def send_tally_request(xml_request: str) -> dict | None:
    """Send XML Request to Tally and return parsed response. Handles Tally errors gracefully."""
    try:
        log(f"Sending data request to {TALLY_URL} with XML: {xml_request[:100]}")
        messagebox.showinfo("Please Wait", "Tally is processing your request.\n\nFor large data or slow devices, this may take up to 2 minutes. Please be patient and do not close Tally or this app.")
        response = requests.post(TALLY_URL, data=xml_request, timeout=120)  # 2 minutes
        log(f"Data request response: status={response.status_code}, text={response.text[:200]}")
        if response.status_code == 200:
            # Check for Tally error in response
            if any(err in response.text for err in ['<LINEERROR>', 'Error in TDL', 'No PARTS', 'No LINES', 'No BUTTONS']):
                log(f"❌ Tally returned error: {response.text}")
                messagebox.showerror("Tally Error", f"Tally returned error. Please check Tally and try again.\n\n{response.text}")
                return None
            if '<ENVELOPE>' not in response.text:
                log(f"❌ Tally response missing <ENVELOPE>: {response.text}")
                messagebox.showerror("Tally Error", f"Tally did not return valid data.\n\n{response.text}")
                return None
            try:
                cleaned_xml = clean_invalid_xml_chars(response.text)
                parsed = xmltodict.parse(cleaned_xml)
                postprocess_vouchers(parsed)
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
    """Fetch Daybook using Custom TDL Report. Make sure your TDL is loaded in Tally and the report name matches exactly."""
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
        accounts = raw_data.get('ENVELOPE', {}).get('BODY', {}).get('DATA', {}).get('TALLYMESSAGE', [])

        if not isinstance(accounts, list):
            accounts = [accounts]  # Ensure it's always a list

        for account in accounts:
            ledger = account.get('LEDGER', {})
            name = ledger.get('@NAME', '')
            under = ledger.get('PARENT', '')  # Category/Group
            opening_balance = ledger.get('OPENINGBALANCE', '0').replace(' Dr', '').replace(' Cr', '').strip()

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

        log(f"✅ Extracted {len(ledgers)} ledgers with opening balances, under category, and amount.")
        return ledgers

    except Exception as e:
        log(f"❌ Error parsing ledger masters: {e}")
        return []


def get_company_name():
    """Extract the company name from Tally using the 'List of Accounts' report as a fallback."""
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
    data = send_tally_request(xml_request)
    try:
        # Try to extract company name from the envelope header if available
        company = data['ENVELOPE']['HEADER'].get('COMPANYNAME')
        if not company:
            # Fallback: try to extract from the first ledger's company attribute
            accounts = data.get('ENVELOPE', {}).get('BODY', {}).get('DATA', {}).get('TALLYMESSAGE', [])
            if isinstance(accounts, list) and accounts:
                ledger = accounts[0].get('LEDGER', {})
                company = ledger.get('COMPANY', None)
        log(f"✅ Extracted company name: {company}")
        return company
    except Exception as e:
        log(f"❌ Error extracting company name: {e}")
        return None


def filter_daybook_vouchers(daybook_data):
    """Filter daybook transactions to only include Sales, Receipt, Payment, Purchase vouchers."""
    allowed_types = {"Sales", "Receipt", "Payment", "Purchase"}
    filtered = []
    try:
        vouchers = daybook_data.get('ENVELOPE', {}).get('BODY', {}).get('DATA', {}).get('TALLYMESSAGE', [])
        if not isinstance(vouchers, list):
            vouchers = [vouchers]
        for v in vouchers:
            voucher = v.get('VOUCHER', {})
            vtype = voucher.get('@VCHTYPE', '')
            if vtype in allowed_types:
                filtered.append(voucher)
        log(f"✅ Filtered {len(filtered)} vouchers of allowed types from daybook.")
        return filtered
    except Exception as e:
        log(f"❌ Error filtering daybook vouchers: {e}")
        return []


def fetch_tally_data() -> dict | None:
    """Fetch only Daybook data from Tally for basic connectivity test."""
    log("🔍 Fetching Daybook Data Only (Basic Test)...")
    raw_daybook = fetch_daybook_data()
    if not raw_daybook:
        log("❌ Failed to fetch daybook data from Tally.")
        return None
    log("✅ Fetched daybook data successfully.")
    # Optionally print a summary of the data
    try:
        vouchers = raw_daybook.get('ENVELOPE', {}).get('BODY', {}).get('DATA', {}).get('TALLYMESSAGE', [])
        log(f"Fetched {len(vouchers)} vouchers from daybook.")
    except Exception as e:
        log(f"Could not summarize daybook data: {e}")
    return {"daybook": raw_daybook}










