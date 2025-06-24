import requests
import os
from requests.adapters import HTTPAdapter
from urllib3.util.retry import Retry
from dotenv import load_dotenv

load_dotenv()

# Load backend URL from environment
BACKEND_URL = os.getenv("BACKEND_URL")

# Setup a session with retries
session = requests.Session()
retries = Retry(total=3, backoff_factor=1, status_forcelist=[500, 502, 503, 504])
session.mount('http://', HTTPAdapter(max_retries=retries))
session.mount('https://', HTTPAdapter(max_retries=retries))


def send_data_to_backend(api_key: str, data_type: str, data: dict) -> bool:
    """
    Send Tally data to Django backend with authentication.

    Args:
        api_key (str): The API Key entered by the user.
        data_type (str): Type of data (e.g., 'daybook', 'ledger').
        data (dict): Parsed Tally data to send.

    Returns:
        bool: True if data sent successfully, False otherwise.
    """
    if not BACKEND_URL:
        print("❌ Backend URL not set.")
        return False

    headers = {'Authorization': f'Bearer {api_key}'}
    payload = {
        "type": data_type,
        "data": data
    }

    try:
        response = session.post(
            f"{BACKEND_URL}/api/receive-tally-data/",
            json=payload,
            headers=headers,
            timeout=10
        )

        if response.status_code == 200:
            print(f"✅ {data_type.capitalize()} data synced successfully.")
            return True
        else:
            print(f"❌ Backend Error [{response.status_code}]: {response.text}")
            return False

    except requests.exceptions.Timeout:
        print(f"❌ Timeout occurred while sending {data_type} to backend.")
        return False

    except Exception as e:
        print(f"❌ Error sending {data_type} to backend: {e}")
        return False
