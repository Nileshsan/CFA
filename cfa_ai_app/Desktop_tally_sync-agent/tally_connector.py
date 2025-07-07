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

TALLY_URL = os.getenv("TALLY_URL", "http://localhost:9000")
log(f"Loaded TALLY_URL: {TALLY_URL}")


def test_tally_connection():
    """Test if Tally is reachable using a simple company info request."""
    test_request = """
    <ENVELOPE>
        <HEADER>
            <TALLYREQUEST>Export Data</TALLYREQUEST>
        </HEADER>
        <BODY>
            <EXPORTDATA>
                <REQUESTDESC>
                    <REPORTNAME>Company Information</REPORTNAME>
                </REQUESTDESC>
            </EXPORTDATA>
        </BODY>
    </ENVELOPE>
    """
    try:
        log(f"Testing connection to {TALLY_URL}")
        response = requests.post(TALLY_URL, data=test_request, timeout=30)
        log(f"Test response: status={response.status_code}, content_length={len(response.text)}")
        
        if response.status_code == 200:
            # Check for common Tally error patterns
            if any(err in response.text for err in ['Error', 'error', 'ERROR', 'No company loaded']):
                log(f"Tally returned error: {response.text[:200]}")
                return False
            return True
        else:
            log(f"HTTP error: {response.status_code}")
            return False
    except requests.exceptions.ConnectionError:
        log("Connection refused - Tally might not be running")
        return False
    except requests.exceptions.Timeout:
        log("Connection timeout")
        return False
    except Exception as e:
        log(f"Connection test failed: {e}")
        return False


def send_tally_request(xml_request: str, timeout: int = 120) -> str | None:
    """Send XML Request to Tally and return raw response."""
    try:
        log(f"Sending request to {TALLY_URL}")
        log(f"Request XML: {xml_request}")
        
        response = requests.post(TALLY_URL, data=xml_request, timeout=timeout)
        log(f"Response status: {response.status_code}")
        log(f"Response length: {len(response.text)} chars")
        
        if response.status_code == 200:
            # Log first 500 characters for debugging
            log(f"Response preview: {response.text[:500]}")
            
            # Check for Tally errors
            error_patterns = [
                'Error in TDL',
                'No such report',
                'Report not found',
                'Invalid report name',
                'No company loaded',
                'Company not available',
                'Access denied'
            ]
            
            response_lower = response.text.lower()
            for pattern in error_patterns:
                if pattern.lower() in response_lower:
                    log(f"Tally error detected: {pattern}")
                    messagebox.showerror("Tally Error", f"Tally returned error: {pattern}")
                    return None
            
            return response.text
        else:
            log(f"HTTP error: {response.status_code}")
            return None
            
    except requests.exceptions.Timeout:
        log("Request timeout")
        messagebox.showerror("Timeout", "Request to Tally timed out. Please try again.")
        return None
    except Exception as e:
        log(f"Request failed: {e}")
        messagebox.showerror("Request Error", f"Failed to send request to Tally: {e}")
        return None


def clean_xml_response(xml_str: str) -> str:
    """Clean and fix XML response from Tally."""
    if not xml_str:
        return None
    
    # Remove BOM if present
    if xml_str.startswith('\ufeff'):
        xml_str = xml_str[1:]
    
    # Remove invalid XML characters
    xml_str = re.sub(r'[^\x09\x0A\x0D\x20-\uD7FF\uE000-\uFFFD]', '', xml_str)
    
    # Decode HTML entities
    xml_str = html.unescape(xml_str)
    
    # Fix common XML issues
    xml_str = xml_str.replace('&', '&amp;')
    xml_str = re.sub(r'&amp;(lt|gt|quot|apos|amp);', r'&\1;', xml_str)
    
    return xml_str


def xml_to_json(xml_str: str) -> str | None:
    """Convert XML string to JSON."""
    try:
        cleaned_xml = clean_xml_response(xml_str)
        if not cleaned_xml:
            return None
        
        # Parse XML
        parsed_dict = xmltodict.parse(cleaned_xml)
        
        # Convert to JSON
        json_str = json.dumps(parsed_dict, indent=2, ensure_ascii=False)
        return json_str
        
    except Exception as e:
        log(f"XML to JSON conversion failed: {e}")
        return None


def fetch_export_data_json(start_date="20240401", end_date="20250630") -> str | None:
    """Fetch data using the custom Export Data XML report."""
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
                        <SVEXPORTFORMAT>XML</SVEXPORTFORMAT>
                        <EXPLODEFLAG>Yes</EXPLODEFLAG>
                    </STATICVARIABLES>
                </REQUESTDESC>
            </EXPORTDATA>
        </BODY>
    </ENVELOPE>
    """
    
    log(f"Fetching export data from {start_date} to {end_date}")
    raw_response = send_tally_request(xml_request)
    
    if raw_response:
        json_response = xml_to_json(raw_response)
        if json_response:
            log("Successfully converted XML to JSON")
            return json_response
        else:
            log("Failed to convert XML to JSON")
            return None
    else:
        log("Failed to get response from Tally")
        return None


def fetch_daybook_standard(start_date="20240401", end_date="20250630") -> str | None:
    """Fetch daybook using standard Tally Day Book report."""
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
                        <SVEXPORTFORMAT>XML</SVEXPORTFORMAT>
                        <EXPLODEFLAG>Yes</EXPLODEFLAG>
                    </STATICVARIABLES>
                </REQUESTDESC>
            </EXPORTDATA>
        </BODY>
    </ENVELOPE>
    """
    
    log(f"Fetching daybook from {start_date} to {end_date}")
    raw_response = send_tally_request(xml_request)
    
    if raw_response:
        json_response = xml_to_json(raw_response)
        if json_response:
            log("Successfully fetched daybook data")
            return json_response
        else:
            log("Failed to convert daybook XML to JSON")
            return None
    else:
        log("Failed to get daybook from Tally")
        return None


def fetch_ledger_list_standard() -> str | None:
    """Fetch ledger list using standard Tally report."""
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
                        <EXPLODEFLAG>Yes</EXPLODEFLAG>
                    </STATICVARIABLES>
                </REQUESTDESC>
            </EXPORTDATA>
        </BODY>
    </ENVELOPE>
    """
    
    log("Fetching ledger list")
    raw_response = send_tally_request(xml_request)
    
    if raw_response:
        json_response = xml_to_json(raw_response)
        if json_response:
            log("Successfully fetched ledger list")
            return json_response
        else:
            log("Failed to convert ledger XML to JSON")
            return None
    else:
        log("Failed to get ledger list from Tally")
        return None


def get_company_name() -> str | None:
    """Get company name from Tally."""
    xml_request = """
    <ENVELOPE>
        <HEADER>
            <TALLYREQUEST>Export Data</TALLYREQUEST>
        </HEADER>
        <BODY>
            <EXPORTDATA>
                <REQUESTDESC>
                    <REPORTNAME>Company Information</REPORTNAME>
                </REQUESTDESC>
            </EXPORTDATA>
        </BODY>
    </ENVELOPE>
    """
    
    try:
        response = send_tally_request(xml_request, timeout=30)
        if response:
            # Try to extract company name from response
            if '<COMPANYNAME>' in response:
                start = response.find('<COMPANYNAME>') + len('<COMPANYNAME>')
                end = response.find('</COMPANYNAME>')
                if end > start:
                    company_name = response[start:end].strip()
                    log(f"Extracted company name: {company_name}")
                    return company_name
            
            # Alternative method - look for company info in XML
            try:
                cleaned_xml = clean_xml_response(response)
                if cleaned_xml:
                    parsed = xmltodict.parse(cleaned_xml)
                    # Try different paths to find company name
                    paths = [
                        'ENVELOPE.HEADER.COMPANYNAME',
                        'ENVELOPE.BODY.DATA.COMPANYNAME',
                        'ENVELOPE.BODY.DATA.TALLYMESSAGE.COMPANYNAME'
                    ]
                    
                    for path in paths:
                        try:
                            company_name = parsed
                            for key in path.split('.'):
                                company_name = company_name[key]
                            if company_name:
                                log(f"Found company name via {path}: {company_name}")
                                return str(company_name)
                        except:
                            continue
            except:
                pass
        
        log("Could not extract company name")
        return None
    except Exception as e:
        log(f"Error getting company name: {e}")
        return None


def test_tdl_report() -> bool:
    """Test if the custom TDL report is available."""
    xml_request = """
    <ENVELOPE>
        <HEADER>
            <TALLYREQUEST>Export Data</TALLYREQUEST>
        </HEADER>
        <BODY>
            <EXPORTDATA>
                <REQUESTDESC>
                    <REPORTNAME>Export Data XML</REPORTNAME>
                </REQUESTDESC>
            </EXPORTDATA>
        </BODY>
    </ENVELOPE>
    """
    
    log("Testing TDL report availability")
    response = send_tally_request(xml_request, timeout=30)
    
    if response and 'TALLYDATAEXPORT' in response:
        log("TDL report is working")
        return True
    else:
        log("TDL report not available or not working")
        return False


# Legacy functions for backward compatibility
def fetch_daybook_data(start_date="20240401", end_date="20250630"):
    """Legacy function - use fetch_daybook_standard instead."""
    return fetch_daybook_standard(start_date, end_date)


def fetch_ledger_details(start_date="20240401", end_date="20250630"):
    """Legacy function - use fetch_ledger_list_standard instead."""
    return fetch_ledger_list_standard()


def fetch_export_data(start_date="20240401", end_date="20250630"):
    """Legacy function - use fetch_export_data_json instead."""
    return fetch_export_data_json(start_date, end_date)


def fetch_tally_data():
    """Test function to fetch basic data."""
    log("Testing basic data fetch")
    
    # First try custom TDL report
    if test_tdl_report():
        log("Using custom TDL report")
        return fetch_export_data_json()
    else:
        log("Using standard reports")
        daybook = fetch_daybook_standard()
        ledgers = fetch_ledger_list_standard()
        
        if daybook or ledgers:
            return {
                "daybook": daybook,
                "ledgers": ledgers
            }
        else:
            log("Failed to fetch any data")
            return None



