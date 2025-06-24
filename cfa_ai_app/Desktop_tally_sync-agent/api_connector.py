import requests
import os
import datetime
from requests.adapters import HTTPAdapter
from urllib3.util.retry import Retry
from dotenv import load_dotenv
from tkinter import messagebox  
import sys

load_dotenv()

# Load backend URL from environment
if getattr(sys, 'frozen', False):
    base_path = sys._MEIPASS
else:
    base_path = os.path.abspath(".")

env_path = os.path.join(base_path, 'config.env')
load_dotenv(dotenv_path=env_path)

# Load backend URL from environment
BACKEND_URL = os.getenv("BACKEND_URL")
# Setup a session with retries
session = requests.Session()
retries = Retry(total=3, backoff_factor=1, status_forcelist=[500, 502, 503, 504])
session.mount('http://', HTTPAdapter(max_retries=retries))
session.mount('https://', HTTPAdapter(max_retries=retries))

# Logging setup
LOG_FILE = os.path.join(os.path.dirname(__file__), 'sync_log.txt')
def log(msg):
    timestamp = datetime.datetime.now().strftime('%Y-%m-%d %H:%M:%S')
    with open(LOG_FILE, 'a', encoding='utf-8') as f:
        f.write(f"[{timestamp}] {msg}\n")
    print(f"[LOG] {msg}")



def send_data_to_backend(api_key: str, data_type: str, data: dict) -> bool:
    """
    Send Tally data to Django backend with authentication.
    """
    if not BACKEND_URL:
        messagebox.showerror("Error", "Backend URL not set in environment.")
        print("❌ Backend URL not set.")
        return False

    headers = {'Authorization': f'Bearer {api_key}'}
    payload = {
        "type": data_type,
        "data": data
    }

    log(f"Sending {data_type} data to backend: {BACKEND_URL}/api/receive-tally-data/ with headers: {headers}")
    try:
        response = session.post(
            f"{BACKEND_URL}/api/receive-tally-data/",
            json=payload,
            headers=headers,
            timeout=10
        )

        log(f"Backend response: status={response.status_code}, text={response.text[:200]}")
        if response.status_code == 200:
            print(f"✅ {data_type.capitalize()} data synced successfully.")
            return True
        else:
            error_message = f"Backend Error [{response.status_code}]: {response.text}"
            messagebox.showerror("Error", error_message)
            print(f"❌ {error_message}")
            return False

    except requests.exceptions.Timeout:
        messagebox.showerror("Error", f"Timeout occurred while sending {data_type} to backend.")
        print(f"❌ Timeout occurred while sending {data_type} to backend.")
        return False

    except Exception as e:
        messagebox.showerror("Error", f"Error sending {data_type} to backend: {e}")
        print(f"❌ Error sending {data_type} to backend: {e}")
        return False
