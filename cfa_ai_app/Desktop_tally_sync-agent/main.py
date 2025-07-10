import os
import sys
import tkinter as tk
from tkinter import messagebox, ttk
from tally_connector import test_tally_connection, fetch_export_data_json, get_company_name
from api_connector import send_data_to_backend, test_backend_connection
from dotenv import load_dotenv
import cv2
import datetime
from PIL import Image, ImageTk
import threading
import json

# Helper to get resource path for PyInstaller
def resource_path(relative_path):
    import sys, os
    if hasattr(sys, '_MEIPASS'):
        return os.path.join(sys._MEIPASS, relative_path)
    return os.path.join(os.path.abspath("."), relative_path)

# DLL path fix for PyInstaller
if getattr(sys, 'frozen', False):
    base_path = getattr(sys, '_MEIPASS', os.path.abspath('.'))
else:
    base_path = os.path.abspath(".")

os.environ['PATH'] += os.pathsep + base_path

# Load environment
load_dotenv()
CONFIG_FILE = "config.env"

# Load configuration from config file
def load_config():
    config = {"API_KEY": "", "TALLY_URL": "http://localhost:9000", "BACKEND_URL": ""}
    if os.path.exists(CONFIG_FILE):
        with open(CONFIG_FILE, "r") as file:
            for line in file:
                if "=" in line:
                    key, value = line.strip().split("=", 1)
                    config[key] = value
    return config

config = load_config()
api_key = config.get("API_KEY", "")

# Logging setup
LOG_FILE = os.path.join(os.path.dirname(__file__), 'sync_log.txt')
def log(msg):
    timestamp = datetime.datetime.now().strftime('%Y-%m-%d %H:%M:%S')
    with open(LOG_FILE, 'a', encoding='utf-8') as f:
        f.write(f"[{timestamp}] {msg}\n")
    print(f"[LOG] {msg}")

# Modern GUI Setup
app = tk.Tk()
app.title("CFA Tally Sync Agent")
app.geometry("550x600")
app.configure(bg="#f8fff8")
app.resizable(False, False)

# Use a simple icon filename for better compatibility
icon_filename = 'appicon.ico'
icon_path = resource_path(f'build_output/{icon_filename}')
try:
    app.iconbitmap(icon_path)
except Exception as e:
    log(f"Failed to set icon: {e}")

# Logo
try:
    logo_img = Image.open(icon_path).resize((64, 64))
    logo_photo = ImageTk.PhotoImage(logo_img)
    logo_label = tk.Label(app, image=logo_photo, bg="#f8fff8")
    logo_label.pack(pady=(10, 0))
except Exception as e:
    log(f"Failed to load logo image: {e}")

# Title
title_label = tk.Label(app, text="CFA Tally Sync Agent", font=("Segoe UI", 22, "bold"), bg="#f8fff8", fg="#2e7d32")
title_label.pack(pady=(5, 10))

# Company Info Frame
company_frame = tk.Frame(app, bg="#f8fff8", relief="sunken", bd=1)
company_frame.pack(pady=5, padx=20, fill="x")
tk.Label(company_frame, text="Company:", font=("Segoe UI", 10, "bold"), bg="#f8fff8").pack(side=tk.LEFT, padx=5)
company_label = tk.Label(company_frame, text="Not Connected", font=("Segoe UI", 10), bg="#f8fff8", fg="#d32f2f")
company_label.pack(side=tk.LEFT, padx=5)

# API Key Entry
api_frame = tk.Frame(app, bg="#f8fff8")
api_frame.pack(pady=10)
tk.Label(api_frame, text="Enter API Key:", font=("Segoe UI", 12), bg="#f8fff8").pack(side=tk.LEFT, padx=(0, 8))
api_entry = ttk.Entry(api_frame, width=36, font=("Segoe UI", 12), show="*")
api_entry.pack(side=tk.LEFT)
api_entry.insert(0, api_key)

# Show/Hide API Key
show_api_var = tk.BooleanVar()
show_api_check = tk.Checkbutton(api_frame, text="Show", variable=show_api_var, command=lambda: toggle_api_visibility(), bg="#f8fff8")
show_api_check.pack(side=tk.LEFT, padx=(5, 0))

def toggle_api_visibility():
    if show_api_var.get():
        api_entry.config(show="")
    else:
        api_entry.config(show="*")

# Button Styles
style = ttk.Style()
style.theme_use('clam')
style.configure('TButton', font=("Segoe UI", 11, "bold"), padding=8, borderwidth=0, relief="flat", background="#b7e4c7", foreground="#2e7d32")
style.map('TButton', background=[('active', '#a5d6a7')])

# Connection Test Buttons
test_frame = tk.Frame(app, bg="#f8fff8")
test_frame.pack(pady=10)
test_tally_btn = ttk.Button(test_frame, text="Test Tally Connection", command=lambda: test_tally_threaded(), width=20)
test_tally_btn.grid(row=0, column=0, padx=5)
test_backend_btn = ttk.Button(test_frame, text="Test Backend Connection", command=lambda: test_backend_threaded(), width=20)
test_backend_btn.grid(row=0, column=1, padx=5)

# API Key Management Buttons
button_frame = tk.Frame(app, bg="#f8fff8")
button_frame.pack(pady=10)
tt_save = ttk.Button(button_frame, text="Save API Key", command=lambda: update_api_key(), width=16)
tt_save.grid(row=0, column=0, padx=8)
tt_qr = ttk.Button(button_frame, text="Scan API Key QR", command=lambda: scan_qr_threaded(), width=16)
tt_qr.grid(row=0, column=1, padx=8)

# Date Range Selection
date_frame = tk.Frame(app, bg="#f8fff8")
date_frame.pack(pady=10)
tk.Label(date_frame, text="Date Range:", font=("Segoe UI", 12), bg="#f8fff8").pack(side=tk.LEFT, padx=(0, 8))
from_date = tk.StringVar(value="20240401")
to_date = tk.StringVar(value="20250630")
tk.Label(date_frame, text="From:", font=("Segoe UI", 10), bg="#f8fff8").pack(side=tk.LEFT, padx=(0, 5))
from_entry = ttk.Entry(date_frame, textvariable=from_date, width=10, font=("Segoe UI", 10))
from_entry.pack(side=tk.LEFT, padx=(0, 10))
tk.Label(date_frame, text="To:", font=("Segoe UI", 10), bg="#f8fff8").pack(side=tk.LEFT, padx=(0, 5))
to_entry = ttk.Entry(date_frame, textvariable=to_date, width=10, font=("Segoe UI", 10))
to_entry.pack(side=tk.LEFT)

# Sync Button
tt_sync = ttk.Button(app, text="Sync Data Now", command=lambda: sync_data_threaded(), width=22)
tt_sync.pack(pady=18)

# Progress Bar
progress = ttk.Progressbar(app, orient="horizontal", length=320, mode="indeterminate")
progress.pack(pady=(0, 10))

# Status Label
status_label = tk.Label(app, text="Ready to sync", font=("Segoe UI", 12), bg="#f8fff8", fg="#2e7d32")
status_label.pack(pady=8)

# Log Display
log_frame = tk.Frame(app, bg="#f8fff8")
log_frame.pack(pady=10, padx=20, fill="both", expand=True)
tk.Label(log_frame, text="Activity Log:", font=("Segoe UI", 10, "bold"), bg="#f8fff8").pack(anchor="w")
log_text = tk.Text(log_frame, height=8, font=("Consolas", 9), bg="#ffffff", fg="#000000", wrap=tk.WORD)
log_scrollbar = ttk.Scrollbar(log_frame, orient="vertical", command=log_text.yview)
log_text.configure(yscrollcommand=log_scrollbar.set)
log_text.pack(side="left", fill="both", expand=True)
log_scrollbar.pack(side="right", fill="y")

def update_log_display(message):
    """Update the log display in the GUI"""
    log_text.insert(tk.END, f"{datetime.datetime.now().strftime('%H:%M:%S')} - {message}\n")
    log_text.see(tk.END)
    app.update_idletasks()

def save_config():
    """Save configuration to config file"""
    with open(CONFIG_FILE, "w") as file:
        file.write(f"API_KEY={api_key}\n")
        file.write(f"TALLY_URL={config.get('TALLY_URL', 'http://localhost:9000')}\n")
        file.write(f"BACKEND_URL={config.get('BACKEND_URL', '')}\n")

def update_api_key():
    global api_key
    entered_key = api_entry.get().strip()
    if entered_key:
        api_key = entered_key
        save_config()
        messagebox.showinfo("Success", "API Key updated successfully!")
        log(f"API Key updated")
        update_log_display("API Key updated successfully")
    else:
        messagebox.showerror("Error", "Please enter a valid API Key")

def scan_qr_threaded():
    threading.Thread(target=scan_qr, daemon=True).start()

def scan_qr():
    global api_key
    update_log_display("Starting QR code scanner...")
    try:
        cap = cv2.VideoCapture(0)
        if not cap.isOpened():
            messagebox.showerror("Error", "Cannot access camera for QR scanning")
            update_log_display("Camera access failed")
            return
            
        detector = cv2.QRCodeDetector()
        found = False
        
        update_log_display("QR scanner ready. Show QR code to camera...")
        while not found:
            ret, frame = cap.read()
            if not ret:
                break

            data, bbox, _ = detector.detectAndDecode(frame)
            if bbox is not None:
                for i in range(len(bbox)):
                    cv2.line(frame, tuple(bbox[i][0]), tuple(bbox[(i + 1) % len(bbox)][0]), color=(183, 228, 199), thickness=2)

                if data:
                    api_key = data.strip()
                    api_entry.delete(0, tk.END)
                    api_entry.insert(0, api_key)
                    save_config()
                    messagebox.showinfo("QR Scan", "API Key Scanned and Saved Successfully!")
                    log(f"API Key scanned from QR")
                    update_log_display("API Key scanned successfully")
                    found = True

            cv2.imshow("Scan QR Code (Press Q to exit)", frame)
            if cv2.waitKey(1) & 0xFF == ord('q'):
                break

        cap.release()
        cv2.destroyAllWindows()
    except Exception as e:
        messagebox.showerror("Error", f"QR scanning failed: {str(e)}")
        update_log_display(f"QR scanning failed: {str(e)}")

def test_tally_threaded():
    threading.Thread(target=test_tally_connection_gui, daemon=True).start()

def test_tally_connection_gui():
    update_log_display("Testing Tally connection...")
    progress.start(10)
    try:
        if test_tally_connection():
            company_name = get_company_name()
            if company_name:
                company_label.config(text=company_name, fg="#388e3c")
                update_log_display(f"Connected to Tally - Company: {company_name}")
                messagebox.showinfo("Success", f"Connected to Tally\nCompany: {company_name}")
            else:
                company_label.config(text="Connected (Unknown Company)", fg="#388e3c")
                update_log_display("Connected to Tally - Company name not found")
                messagebox.showinfo("Success", "Connected to Tally")
        else:
            company_label.config(text="Not Connected", fg="#d32f2f")
            update_log_display("Failed to connect to Tally")
            messagebox.showerror("Error", "Failed to connect to Tally")
    except Exception as e:
        update_log_display(f"Tally connection test failed: {str(e)}")
        messagebox.showerror("Error", f"Tally connection test failed: {str(e)}")
    finally:
        progress.stop()

def test_backend_threaded():
    threading.Thread(target=test_backend_connection_gui, daemon=True).start()

def test_backend_connection_gui():
    if not api_key:
        messagebox.showerror("Error", "Please enter API Key first")
        return
    
    update_log_display("Testing backend connection...")
    progress.start(10)
    try:
        if test_backend_connection(api_key):
            update_log_display("Backend connection successful")
            messagebox.showinfo("Success", "Backend connection successful")
        else:
            update_log_display("Backend connection failed")
            messagebox.showerror("Error", "Backend connection failed")
    except Exception as e:
        update_log_display(f"Backend connection test failed: {str(e)}")
        messagebox.showerror("Error", f"Backend connection test failed: {str(e)}")
    finally:
        progress.stop()

def sync_data_threaded():
    threading.Thread(target=sync_data, daemon=True).start()

def sync_data():
    log("Sync Data button clicked.")
    update_log_display("Starting data sync...")
    
    if not api_key:
        messagebox.showerror("Error", "API Key not set. Please enter or scan API Key first.")
        log("API Key not set. Sync aborted.")
        update_log_display("Sync aborted - API Key not set")
        return

    # Disable sync button during operation
    tt_sync.config(state='disabled')
    
    try:
        status_label.config(text="Connecting to Tally...", fg="#2e7d32")
        progress.start(10)
        app.update_idletasks()
        update_log_display("Connecting to Tally...")

        if not test_tally_connection():
            messagebox.showerror("Error", "Tally not connected. Please open Tally and load the company.")
            status_label.config(text="Tally not connected.", fg="#d32f2f")
            progress.stop()
            log("Tally not connected. Sync aborted.")
            update_log_display("Sync aborted - Tally not connected")
            return

        # Get company name for logging
        company_name = get_company_name()
        if company_name:
            update_log_display(f"Connected to Tally - Company: {company_name}")
            company_label.config(text=company_name, fg="#388e3c")

        status_label.config(text="Fetching data from Tally...", fg="#2e7d32")
        app.update_idletasks()
        log("Tally connected. Fetching data...")
        update_log_display("Fetching data from Tally...")

        # Get date range
        start_date = from_date.get().strip()
        end_date = to_date.get().strip()
        
        if not start_date or not end_date:
            start_date = "20240401"
            end_date = "20250630"
            
        update_log_display(f"Date range: {start_date} to {end_date}")

        # Fetch data as JSON
        all_data_json = fetch_export_data_json(start_date, end_date)
        
        if all_data_json:
            # Parse JSON to get record counts
            try:
                data_obj = json.loads(all_data_json)
                voucher_count = 0
                ledger_count = 0
                
                # Count vouchers and ledgers
                if 'TALLYDATAEXPORT' in data_obj:
                    vouchers = data_obj['TALLYDATAEXPORT'].get('VOUCHERS', {})
                    if isinstance(vouchers, dict) and 'VOUCHER' in vouchers:
                        voucher_data = vouchers['VOUCHER']
                        voucher_count = len(voucher_data) if isinstance(voucher_data, list) else 1
                    
                    ledgers = data_obj['TALLYDATAEXPORT'].get('LEDGERS', {})
                    if isinstance(ledgers, dict) and 'LEDGER' in ledgers:
                        ledger_data = ledgers['LEDGER']
                        ledger_count = len(ledger_data) if isinstance(ledger_data, list) else 1
                
                update_log_display(f"Fetched {voucher_count} vouchers and {ledger_count} ledgers")
            except:
                update_log_display("Data fetched successfully")
            
            status_label.config(text="Sending data to backend...", fg="#2e7d32")
            app.update_idletasks()
            log("Data fetched from Tally as JSON. Sending to backend...")
            update_log_display("Sending data to backend...")
            
            success = send_data_to_backend(api_key, "export_json", all_data_json, is_json=True)
            
            if success:
                messagebox.showinfo("Success", "Data synced successfully!")
                status_label.config(text="Data synced successfully!", fg="#388e3c")
                log("Data synced to backend successfully.")
                update_log_display("Data synced successfully!")
            else:
                messagebox.showerror("Error", "Failed to send data to backend.")
                status_label.config(text="Sync failed. Check logs.", fg="#fbc02d")
                log("Failed to sync data to backend.")
                update_log_display("Failed to send data to backend")
        else:
            messagebox.showerror("Error", "No data fetched from Tally.")
            status_label.config(text="No data fetched.", fg="#d32f2f")
            log("No data fetched from Tally.")
            update_log_display("No data fetched from Tally")
            
    except Exception as e:
        messagebox.showerror("Error", f"Sync failed: {str(e)}")
        status_label.config(text="Sync failed with error.", fg="#d32f2f")
        log(f"Sync failed with error: {str(e)}")
        update_log_display(f"Sync failed: {str(e)}")
    finally:
        progress.stop()
        tt_sync.config(state='normal')

# Initialize GUI
update_log_display("CFA Tally Sync Agent started")
if api_key:
    update_log_display("API Key loaded from config")
else:
    update_log_display("No API Key found - please configure")

app.mainloop()


