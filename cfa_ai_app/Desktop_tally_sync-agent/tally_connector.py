import requests
import xmltodict
import os
from dotenv import load_dotenv

load_dotenv()

TALLY_URL = os.getenv("TALLY_URL")
API_KEY = os.getenv("API_KEY")
BACKEND_URL = os.getenv("BACKEND_URL")  # URL to send data to Django

def test_tally_connection():
    """Test connection with Tally Server"""
    try:
        response = requests.get(TALLY_URL)
        return response.status_code == 200
    except Exception as e:
        print("Connection failed:", e)
        return False

def fetch_daybook_data():
    """Fetch transaction data from Daybook (Sales, Purchase, Receipt, Payment)"""
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
                        <SVFROMDATE>20240401</SVFROMDATE>  <!-- Start Date -->
                        <SVTODATE>20250630</SVTODATE>      <!-- End Date -->
                        <EXPLODEFLAG>Yes</EXPLODEFLAG>
                        <SVEXPORTFORMAT>XML</SVEXPORTFORMAT>
                    </STATICVARIABLES>
                </REQUESTDESC>
            </EXPORTDATA>
        </BODY>
    </ENVELOPE>
    """
    return send_tally_request(xml_request)

def fetch_ledger_data():
    """Fetch Ledger List (Opening Balances)"""
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
                        <SVEXPORTFORMAT>XML</SVEXPORTFORMAT>
                    </STATICVARIABLES>
                </REQUESTDESC>
            </EXPORTDATA>
        </BODY>
    </ENVELOPE>
    """
    return send_tally_request(xml_request)

def send_tally_request(xml_request):
    """Send XML Request to Tally and parse response"""
    try:
        response = requests.post(TALLY_URL, data=xml_request)
        if response.status_code == 200:
            return xmltodict.parse(response.text)
        else:
            print(f"Error: Status Code {response.status_code}")
            return None
    except Exception as e:
        print("Error fetching data:", e)
        return None

def push_data_to_backend(data_type, data):
    """Push Tally data to Django backend"""
    try:
        response = requests.post(
            f"{BACKEND_URL}/api/receive-tally-data/",
            json={"type": data_type, "data": data},
            headers={'Authorization': f'Bearer {API_KEY}'}
        )
        if response.status_code == 200:
            print(f"{data_type} sync successful.")
        else:
            print(f"{data_type} sync failed with status {response.status_code}")
    except Exception as e:
        print(f"Error sending {data_type} to backend:", e)

def run_sync():
    """Run full sync process"""
    if not test_tally_connection():
        print("Tally is not connected.")
        return

    print("Syncing Daybook...")
    daybook_data = fetch_daybook_data()
    if daybook_data:
        push_data_to_backend("daybook", daybook_data)

    print("Syncing Ledger...")
    ledger_data = fetch_ledger_data()
    if ledger_data:
        push_data_to_backend("ledger", ledger_data)

    print("Sync Completed Successfully.")

if __name__ == "__main__":
    run_sync()
