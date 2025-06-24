import requests
import xmltodict
import os
from dotenv import load_dotenv

load_dotenv()

TALLY_URL = os.getenv("TALLY_URL")


def test_tally_connection() -> bool:
    """Test if Tally is reachable."""
    try:
        response = requests.get(TALLY_URL, timeout=5)
        return response.status_code == 200
    except Exception as e:
        print(f"❌ Connection failed: {e}")
        return False


def send_tally_request(xml_request: str) -> dict | None:
    """Send XML Request to Tally and return parsed response."""
    try:
        response = requests.post(TALLY_URL, data=xml_request, timeout=10)
        if response.status_code == 200:
            return xmltodict.parse(response.text)
        else:
            print(f"❌ Tally responded with status: {response.status_code}")
            return None
    except Exception as e:
        print(f"❌ Error fetching data from Tally: {e}")
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
    print("🔍 Fetching Daybook Data...")
    daybook_data = fetch_daybook_data()

    print("🔍 Fetching Ledger Details...")
    ledger_data = fetch_ledger_details()

    if not daybook_data or not ledger_data:
        print("❌ Failed to fetch some data from Tally.")
        return None

    print("✅ Fetched Daybook and Ledger successfully.")
    return {"daybook": daybook_data, "ledger": ledger_data}


