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
    """Properly test if Tally is reachable using a valid XML request."""
    test_request = """
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


def fetch_tally_data() -> dict | None:
    """Fetch both Daybook and Ledger Data from Tally."""
    log("🔍 Fetching Daybook Data...")
    daybook_data = fetch_daybook_data()

    log("🔍 Fetching Ledger Details...")
    ledger_data = fetch_ledger_details()

    if not daybook_data or not ledger_data:
        log("❌ Failed to fetch some data from Tally.")
        return None

    log("✅ Fetched Daybook and Ledger successfully.")
    return {"daybook": daybook_data, "ledger": ledger_data}


