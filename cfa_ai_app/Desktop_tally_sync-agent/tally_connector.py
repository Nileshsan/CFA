import requests
import xmltodict
import os
from dotenv import load_dotenv
import sys
import datetime

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
    """Test if Tally is reachable using a valid XML request (Company Info)."""
    test_request = """
    <ENVELOPE>
        <HEADER>
            <TALLYREQUEST>Export Data</TALLYREQUEST>
        </HEADER>
        <BODY>
            <EXPORTDATA>
                <REQUESTDESC>
                    <REPORTNAME>Company Info</REPORTNAME>
                </REQUESTDESC>
            </EXPORTDATA>
        </BODY>
    </ENVELOPE>
    """
    try:
        log(f"Sending test connection POST to {TALLY_URL}")
        response = requests.post(TALLY_URL, data=test_request, timeout=5)
        log(f"Test connection response: status={response.status_code}, text={response.text[:200]}")
        if response.status_code == 200 and "<ENVELOPE>" in response.text:
            return True
        else:
            log(f"❌ Invalid response from Tally: {response.text}")
            return False
    except Exception as e:
        log(f"❌ Connection failed: {e}")
        return False


def send_tally_request(xml_request: str) -> dict | None:
    """Send XML Request to Tally and return parsed response."""
    try:
        log(f"Sending data request to {TALLY_URL} with XML: {xml_request[:100]}")
        response = requests.post(TALLY_URL, data=xml_request, timeout=10)
        log(f"Data request response: status={response.status_code}, text={response.text[:200]}")
        if response.status_code == 200:
            return xmltodict.parse(response.text)
        else:
            log(f"❌ Tally responded with status: {response.status_code}")
            return None
    except Exception as e:
        log(f"❌ Error fetching data from Tally: {e}")
        return None


def fetch_daybook_data(start_date="20240401", end_date="20250630") -> dict | None:
    """Fetch Full Transaction Daybook from Tally."""
    xml_request = f"""
    <ENVELOPE>
        <HEADER>
            <TALLYREQUEST>Export Data</TALLYREQUEST>
        </HEADER>
        <BODY>
            <EXPORTDATA>
                <REQUESTDESC>
                    <REPORTNAME>Daybook</REPORTNAME>
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
    """Fetch Detailed Ledger Information including opening balances."""
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


def fetch_ledger_masters() -> list:
    """Fetch all ledger masters with opening balances."""
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
            opening_balance = ledger.get('OPENINGBALANCE', '0').replace(' Dr', '').replace(' Cr', '').strip()

            try:
                opening_balance_value = float(opening_balance)
            except ValueError:
                opening_balance_value = 0

            if opening_balance_value != 0:
                ledgers.append({
                    "name": name,
                    "opening_balance": opening_balance_value
                })

        log(f"✅ Extracted {len(ledgers)} ledgers with opening balances.")
        return ledgers

    except Exception as e:
        log(f"❌ Error parsing ledger masters: {e}")
        return []


def get_company_name():
    """Extract the company name from Tally using the 'Company Info' report."""
    xml_request = """
    <ENVELOPE>
        <HEADER>
            <TALLYREQUEST>Export Data</TALLYREQUEST>
        </HEADER>
        <BODY>
            <EXPORTDATA>
                <REQUESTDESC>
                    <REPORTNAME>Company Info</REPORTNAME>
                    <STATICVARIABLES>
                        <SVEXPORTFORMAT>XML</SVEXPORTFORMAT>
                    </STATICVARIABLES>
                </REQUESTDESC>
            </EXPORTDATA>
        </BODY>
    </ENVELOPE>
    """
    data = send_tally_request(xml_request)
    try:
        company = data['ENVELOPE']['BODY']['DATA']['TALLYMESSAGE']['COMPANYINFO']['COMPANY']['@NAME']
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
    """Fetch company name, ledgers, and filtered daybook data from Tally."""
    log("🔍 Fetching Company Name...")
    company_name = get_company_name()
    log("🔍 Fetching Ledger Masters...")
    ledgers = fetch_ledger_masters()
    log("🔍 Fetching Daybook Data...")
    raw_daybook = fetch_daybook_data()
    filtered_daybook = filter_daybook_vouchers(raw_daybook) if raw_daybook else []
    if not company_name or not ledgers or not filtered_daybook:
        log("❌ Failed to fetch some data from Tally.")
        return None
    log("✅ Fetched company, ledgers, and daybook successfully.")
    return {
        "company": company_name,
        "ledgers": ledgers,
        "transactions": filtered_daybook
    }










