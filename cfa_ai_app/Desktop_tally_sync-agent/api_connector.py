import requests
import os
import sys
import json
import datetime
from typing import Optional, Dict, Any, Union
from requests.adapters import HTTPAdapter
from urllib3.util.retry import Retry
from dotenv import load_dotenv
from tkinter import messagebox
import urllib.parse


class APIConnector:
    """Enhanced API Connector for Tally data synchronization with Django backend."""
    
    def __init__(self):
        """Initialize the API connector with configuration and session setup."""
        self._setup_logging()  # Ensure log_file is set before any log calls
        self._load_environment()
        self._setup_session()
        
    def _load_environment(self) -> None:
        """Load environment variables from config file."""
        load_dotenv()
        
        # Determine base path for PyInstaller compatibility
        if getattr(sys, 'frozen', False):
            base_path = getattr(sys, '_MEIPASS', os.path.abspath("."))
        else:
            base_path = os.path.abspath(".")
        
        # Load from config.env file
        env_path = os.path.join(base_path, 'config.env')
        load_dotenv(dotenv_path=env_path)
        
        # Get backend URL and validate
        self.backend_url = os.getenv("BACKEND_URL", "").strip()
        if not self.backend_url:
            self.log("⚠️ Backend URL not set in environment variables")
        else:
            # Ensure URL doesn't end with slash for consistency
            self.backend_url = self.backend_url.rstrip('/')
            self.log(f"✅ Backend URL loaded: {self.backend_url}")
    
    def _setup_session(self) -> None:
        """Setup requests session with retry strategy and timeouts."""
        self.session = requests.Session()
        
        # Configure retry strategy
        retry_strategy = Retry(
            total=3,
            backoff_factor=1,
            status_forcelist=[500, 502, 503, 504, 429],  # Added 429 for rate limiting
            allowed_methods=["HEAD", "GET", "OPTIONS", "POST"],
            raise_on_status=False
        )
        
        # Mount adapters with retry strategy
        adapter = HTTPAdapter(max_retries=retry_strategy)
        self.session.mount('http://', adapter)
        self.session.mount('https://', adapter)
        
        # Set default headers
        self.session.headers.update({
            'User-Agent': 'CFA-Tally-Sync-Agent/1.0',
            'Accept': 'application/json',
            'Connection': 'keep-alive'
        })
    
    def _setup_logging(self) -> None:
        """Setup logging configuration."""
        self.log_file = os.path.join(os.path.dirname(__file__), 'sync_log.txt')
        
        # Ensure log directory exists
        log_dir = os.path.dirname(self.log_file)
        if not os.path.exists(log_dir):
            os.makedirs(log_dir)
    
    def log(self, msg: str, suppress_terminal: bool = False) -> None:
        """Enhanced logging with timestamp and error handling. Optionally suppress terminal output."""
        timestamp = datetime.datetime.now().strftime('%Y-%m-%d %H:%M:%S')
        log_entry = f"[{timestamp}] {msg}\n"
        
        try:
            with open(self.log_file, 'a', encoding='utf-8') as f:
                f.write(log_entry)
        except Exception as e:
            print(f"[LOG ERROR] Failed to write to log file: {e}")
        if not suppress_terminal:
            print(f"[API_CONNECTOR] {msg}")
    
    def _validate_api_key(self, api_key: str) -> bool:
        """Validate API key format and presence."""
        if not api_key or not isinstance(api_key, str):
            self.log("❌ Invalid API key: empty or not a string")
            return False
        
        api_key = api_key.strip()
        if len(api_key) < 10:  # Minimum reasonable length
            self.log("❌ Invalid API key: too short")
            return False
        
        return True
    
    def _prepare_headers(self, api_key: str, is_json: bool = False) -> Dict[str, str]:
        """Prepare request headers with authentication and content type."""
        headers = {
            'Authorization': f'Bearer {api_key}',
            'X-Timestamp': str(int(datetime.datetime.now().timestamp())),
            'X-Client-Version': '1.0'
        }
        
        if is_json:
            headers['Content-Type'] = 'application/json'
        
        return headers
    
    def _prepare_payload(self, data_type: str, data: Any, is_json: bool = False) -> Union[str, Dict[str, Any]]:
        """Prepare request payload based on data type."""
        if is_json:
            if isinstance(data, str):
                # Validate JSON string
                try:
                    json.loads(data)
                    return data
                except json.JSONDecodeError as e:
                    self.log(f"❌ Invalid JSON data: {e}")
                    raise ValueError(f"Invalid JSON data: {e}")
            else:
                # Convert to JSON string
                try:
                    return json.dumps(data, ensure_ascii=False)
                except (TypeError, ValueError) as e:
                    self.log(f"❌ Failed to serialize data to JSON: {e}")
                    raise ValueError(f"Failed to serialize data to JSON: {e}")
        else:
            return {
                "type": data_type,
                "data": data,
                "timestamp": datetime.datetime.now().isoformat(),
                "client_version": "1.0"
            }
    
    def _handle_response(self, response: requests.Response, data_type: str) -> bool:
        """Handle API response with detailed error reporting."""
        try:
            # Log response details
            self.log(f"Backend response: status={response.status_code}, "
                    f"headers={dict(response.headers)}, text={response.text[:200]}")
            
            if response.status_code in (200, 201):
                # Try to parse response as JSON for additional info
                try:
                    response_data = response.json()
                    if isinstance(response_data, dict):
                        message = response_data.get('message', 'Data synced successfully')
                        self.log(f"✅ {data_type.capitalize()} sync successful: {message}")
                    else:
                        self.log(f"✅ {data_type.capitalize()} data synced successfully")
                except json.JSONDecodeError:
                    self.log(f"✅ {data_type.capitalize()} data synced successfully")
                
                return True
            
            elif response.status_code == 401:
                error_msg = "Authentication failed. Please check your API key."
                self.log(f"❌ Authentication error: {error_msg}")
                messagebox.showerror("Authentication Error", error_msg)
                return False
            
            elif response.status_code == 403:
                error_msg = "Access denied. You don't have permission to perform this action."
                self.log(f"❌ Authorization error: {error_msg}")
                messagebox.showerror("Authorization Error", error_msg)
                return False
            
            elif response.status_code == 413:
                error_msg = "Data payload too large. Please try with smaller date ranges."
                self.log(f"❌ Payload too large: {error_msg}")
                messagebox.showerror("Data Size Error", error_msg)
                return False
            
            elif response.status_code == 429:
                error_msg = "Rate limit exceeded. Please wait before retrying."
                self.log(f"❌ Rate limit error: {error_msg}")
                messagebox.showerror("Rate Limit Error", error_msg)
                return False
            
            elif 400 <= response.status_code < 500:
                error_msg = f"Client error [{response.status_code}]: {response.text}"
                self.log(f"❌ Client error: {error_msg}")
                messagebox.showerror("Client Error", error_msg)
                return False
            
            elif 500 <= response.status_code < 600:
                error_msg = f"Server error [{response.status_code}]: {response.text}"
                self.log(f"❌ Server error: {error_msg}")
                messagebox.showerror("Server Error", error_msg)
                return False
            
            else:
                error_msg = f"Unexpected response [{response.status_code}]: {response.text}"
                self.log(f"❌ Unexpected response: {error_msg}")
                messagebox.showerror("Unexpected Error", error_msg)
                return False
        
        except Exception as e:
            self.log(f"❌ Error handling response: {e}")
            messagebox.showerror("Response Error", f"Error processing server response: {e}")
            return False
    
    def test_backend_connection(self, api_key: str) -> bool:
        """Test connection to backend with health check endpoint."""
        if not self.backend_url:
            messagebox.showerror("Configuration Error", "Backend URL not configured.")
            self.log("❌ Backend URL not configured")
            return False
        
        if not self._validate_api_key(api_key):
            messagebox.showerror("Authentication Error", "Invalid API key.")
            return False
        
        try:
            headers = self._prepare_headers(api_key)
            test_url = f"{self.backend_url}/api/health/"
            
            self.log(f"Testing backend connection to: {test_url}")
            
            response = self.session.get(
                test_url,
                headers=headers,
                timeout=10
            )
            
            if response.status_code == 200:
                self.log("✅ Backend connection test successful")
                return True
            else:
                self.log(f"❌ Backend connection test failed: {response.status_code}")
                return False
        
        except requests.exceptions.Timeout:
            self.log("❌ Backend connection test timed out")
            messagebox.showerror("Connection Error", "Backend connection test timed out.")
            return False
        
        except requests.exceptions.ConnectionError:
            self.log("❌ Backend connection test failed: Connection error")
            messagebox.showerror("Connection Error", "Cannot connect to backend server.")
            return False
        
        except Exception as e:
            self.log(f"❌ Backend connection test failed: {e}")
            messagebox.showerror("Connection Error", f"Backend connection test failed: {e}")
            return False
    
    def send_data_to_backend(self, api_key: str, data_type: str, data: Any, is_json: bool = False) -> bool:
        """
        Send Tally data to Django backend with enhanced error handling and payload validation.
        
        Args:
            api_key: Authentication API key
            data_type: Type of data being sent
            data: Data payload (dict, list, or JSON string)
            is_json: Whether data is already a JSON string
            
        Returns:
            bool: True if successful, False otherwise
        """
        # Validate inputs
        if not self.backend_url:
            messagebox.showerror("Configuration Error", "Backend URL not configured.")
            self.log("❌ Backend URL not configured")
            return False
        
        if not self._validate_api_key(api_key):
            messagebox.showerror("Authentication Error", "Invalid API key.")
            return False
        
        if not data_type:
            self.log("❌ Data type not specified")
            messagebox.showerror("Data Error", "Data type not specified.")
            return False
        
        # --- Enhanced payload validation and logging ---
        if data_type in ["transactions", "vouchers"]:
            # If data is a JSON string, try to parse it
            tx_data = None
            if is_json:
                try:
                    tx_data = json.loads(data) if isinstance(data, str) else data
                except Exception as e:
                    self.log(f"❌ Failed to parse JSON transaction data: {e}")
                    messagebox.showerror("Data Error", f"Failed to parse transaction JSON: {e}")
                    return False
            else:
                tx_data = data
            # --- Do NOT require or attach company_name for backend ---
            # Validate non-empty list
            if not isinstance(tx_data, list) or not tx_data:
                self.log(f"❌ Transaction payload is empty or not a list: {tx_data}")
                messagebox.showerror("Data Error", "Transaction data must be a non-empty list.")
                return False
            # Validate required fields in each transaction
            required_fields = ["party_name", "voucher_no", "voucher_type", "date", "amount", "ledger_entries"]
            for idx, tx in enumerate(tx_data):
                if not isinstance(tx, dict):
                    self.log(f"❌ Transaction at index {idx} is not a dict: {tx}")
                    messagebox.showerror("Data Error", f"Transaction at index {idx} is not a dict.")
                    return False
                missing = [f for f in required_fields if f not in tx]
                if missing:
                    self.log(f"❌ Transaction at index {idx} missing fields: {missing}")
                    messagebox.showerror("Data Error", f"Transaction at index {idx} missing fields: {missing}")
                    return False
            # Pretty-print payload for logging
            try:
                pretty_payload = json.dumps(tx_data, indent=2, ensure_ascii=False)
                payload_path = os.path.join(os.path.dirname(__file__), 'last_transaction_payload.json')
                with open(payload_path, 'w', encoding='utf-8') as f:
                    f.write(pretty_payload)
                # --- Save a copy in file_backend directory ---
                backend_dir = os.path.join(os.path.dirname(__file__), 'file_backend')
                os.makedirs(backend_dir, exist_ok=True)
                backend_file = os.path.join(backend_dir, f'{data_type}_payload_{datetime.datetime.now().strftime("%Y%m%d_%H%M%S")}.json')
                with open(backend_file, 'w', encoding='utf-8') as f:
                    f.write(pretty_payload)
                self.log(f"Outgoing transaction payload saved to: {payload_path}", suppress_terminal=True)
                self.log(f"Copy also saved to: {backend_file}", suppress_terminal=True)
            except Exception as e:
                self.log(f"Failed to save outgoing transaction payload: {e}")
        else:
            # Log other data types
            try:
                pretty_payload = json.dumps(data, indent=2, ensure_ascii=False) if not is_json else str(data)
                self.log(f"Outgoing {data_type} payload:\n{pretty_payload}")
                # --- Save a copy in file_backend directory ---
                backend_dir = os.path.join(os.path.dirname(__file__), 'file_backend')
                os.makedirs(backend_dir, exist_ok=True)
                ext = 'json' if not is_json else 'txt'
                backend_file = os.path.join(backend_dir, f'{data_type}_payload_{datetime.datetime.now().strftime("%Y%m%d_%H%M%S")}.{ext}')
                with open(backend_file, 'w', encoding='utf-8') as f:
                    f.write(pretty_payload)
                self.log(f"Copy also saved to: {backend_file}", suppress_terminal=True)
            except Exception as e:
                self.log(f"Outgoing {data_type} payload: {data} (pretty-print failed: {e})")
        
        try:
            headers = self._prepare_headers(api_key, is_json=True)
            payload = self._prepare_payload(data_type, data, is_json=is_json)
            
            # Determine URL based on data type
            if data_type in ["transactions", "vouchers"]:
                url = f"{self.backend_url}/api/transactions/"
            elif data_type == "masters":
                url = f"{self.backend_url}/api/sync/masters/"
            else:
                self.log(f"❌ Unknown data type: {data_type}")
                messagebox.showerror("Data Error", f"Unknown data type: {data_type}")
                return False
            
            self.log(f"Sending {data_type} data to backend: {url}")
            
            response = self.session.post(
                url,
                headers=headers,
                data=payload,
                timeout=10
            )
            
            return self._handle_response(response, data_type)
        
        except requests.exceptions.Timeout:
            self.log("❌ Request timed out")
            messagebox.showerror("Request Error", "The request to the backend timed out.")
            return False
        
        except requests.exceptions.ConnectionError:
            self.log("❌ Request failed: Connection error")
            messagebox.showerror("Request Error", "Cannot connect to backend server.")
            return False
        
        except Exception as e:
            self.log(f"❌ Request failed: {e}")
            messagebox.showerror("Request Error", f"Request failed: {e}")
            return False
    
    def close(self) -> None:
        """Close the session and cleanup resources."""
        if hasattr(self, 'session'):
            self.session.close()
            self.log("✅ API connector session closed")

# Global instance for backward compatibility
_api_connector = APIConnector()

# Backward compatibility functions

def log(msg: str) -> None:
    """Legacy logging function for backward compatibility."""
    _api_connector.log(msg)

def send_data_to_backend(api_key: str, data_type: str, data: Any, is_json: bool = False) -> bool:
    """Legacy function for backward compatibility."""
    return _api_connector.send_data_to_backend(api_key, data_type, data, is_json)

def test_backend_connection(api_key: str) -> bool:
    """Legacy function for backward compatibility."""
    return _api_connector.test_backend_connection(api_key)

# Cleanup on module exit
import atexit
atexit.register(_api_connector.close)





