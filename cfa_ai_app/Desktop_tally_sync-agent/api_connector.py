import requests
import os
from dotenv import load_dotenv

load_dotenv()

API_KEY = os.getenv("API_KEY")
BACKEND_URL = os.getenv("BACKEND_URL")

def send_data_to_backend(data_type, data):
    """
    Send Tally data to Django backend with authentication.
    
    Args:
        data_type (str): Type of data (e.g., 'daybook', 'ledger', 'opening_balance').
        data (dict): Parsed Tally data to send.
    
    Returns:
        bool: True if data sent successfully, False otherwise.
    """
    headers = {'Authorization': f'Bearer {API_KEY}'}
    payload = {
        "type": data_type,  # Example: "daybook", "ledger", etc.
        "data": data
    }

    try:
        response = requests.post(f"{BACKEND_URL}/api/receive-tally-data/", json=payload, headers=headers)
        if response.status_code == 200:
            print(f"✅ {data_type.capitalize()} data synced successfully.")
            return True
        else:
            print(f"❌ Backend Error [{response.status_code}]: {response.text}")
            return False
    except Exception as e:
        print(f"❌ Error sending {data_type} to backend:", e)
        return False
