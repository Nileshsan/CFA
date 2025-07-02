import os
import sys
import tkinter as tk
from tkinter import messagebox, ttk
from tally_connector import test_tally_connection, fetch_tally_data
from api_connector import send_data_to_backend
from dotenv import load_dotenv
import cv2
import datetime
from PIL import Image, ImageTk
import threading

# Helper to get resource path for PyInstaller
def resource_path(relative_path):
    if hasattr(sys, '_MEIPASS'):
        return os.path.join(sys._MEIPASS, relative_path)
    return os.path.join(os.path.abspath("."), relative_path)

# DLL path fix for PyInstaller
if getattr(sys, 'frozen', False):
    base_path = sys._MEIPASS
else:
    base_path = os.path.abspath(".")

os.environ['PATH'] += os.pathsep + base_path

# Load environment
load_dotenv()
CONFIG_FILE = "config.env"

# Load API key from config
api_key = ""
if os.path.exists(CONFIG_FILE):
    with open(CONFIG_FILE, "r") as file:
        for line in file:
            if line.startswith("API_KEY="):
                api_key = line.strip().split("=")[1]

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
app.geometry("500x480")
app.configure(bg="#f8fff8")
app.iconbitmap(resource_path('build_output/icon.ico'))

# Logo
logo_path = resource_path('build_output/icon.ico')
logo_img = Image.open(logo_path).resize((64, 64))
logo_photo = ImageTk.PhotoImage(logo_img)
logo_label = tk.Label(app, image=logo_photo, bg="#f8fff8")
logo_label.pack(pady=(18, 6))

# Title
tk.Label(app, text="CFA Tally Sync Agent", font=("Segoe UI", 22, "bold"), bg="#f8fff8", fg="#2e7d32").pack(pady=(0, 10))

# API Key Entry
api_frame = tk.Frame(app, bg="#f8fff8")
api_frame.pack(pady=5)
tk.Label(api_frame, text="Enter API Key:", font=("Segoe UI", 12), bg="#f8fff8").pack(side=tk.LEFT, padx=(0, 8))
api_entry = ttk.Entry(api_frame, width=36, font=("Segoe UI", 12))
api_entry.pack(side=tk.LEFT)
api_entry.insert(0, api_key)

# Button Styles
style = ttk.Style()
style.theme_use('clam')
style.configure('TButton', font=("Segoe UI", 11, "bold"), padding=8, borderwidth=0, relief="flat", background="#b7e4c7", foreground="#2e7d32")
style.map('TButton', background=[('active', '#a5d6a7')])

button_frame = tk.Frame(app, bg="#f8fff8")
button_frame.pack(pady=10)

tt_save = ttk.Button(button_frame, text="Save API Key", command=lambda: update_api_key(), width=16)
tt_save.grid(row=0, column=0, padx=8)
tt_qr = ttk.Button(button_frame, text="Scan API Key QR", command=lambda: scan_qr(), width=16)
tt_qr.grid(row=0, column=1, padx=8)

tt_sync = ttk.Button(app, text="Sync Data Now", command=lambda: sync_data_threaded(), width=22)
tt_sync.pack(pady=18)

# Progress Bar
progress = ttk.Progressbar(app, orient="horizontal", length=320, mode="indeterminate")
progress.pack(pady=(0, 10))

status_label = tk.Label(app, text="", font=("Segoe UI", 12), bg="#f8fff8")
status_label.pack(pady=8)

def save_api_key_to_config(key):
    with open(CONFIG_FILE, "w") as file:
        file.write(f"API_KEY={key}\n")
    messagebox.showinfo("Success", "API Key saved successfully!")

def update_api_key():
    global api_key
    entered_key = api_entry.get().strip()
    if entered_key:
        api_key = entered_key
        save_api_key_to_config(api_key)
        messagebox.showinfo("Success", "API Key updated successfully!")
        log(f"API Key updated to: {api_key}")

def scan_qr():
    global api_key
    cap = cv2.VideoCapture(0)
    detector = cv2.QRCodeDetector()
    found = False

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
                save_api_key_to_config(api_key)
                messagebox.showinfo("QR Scan", "API Key Scanned and Saved Successfully!")
                log(f"API Key scanned from QR: {api_key}")
                found = True

        cv2.imshow("Scan QR Code (Press Q to exit)", frame)
        if cv2.waitKey(1) & 0xFF == ord('q'):
            break

    cap.release()
    cv2.destroyAllWindows()

def sync_data_threaded():
    threading.Thread(target=sync_data, daemon=True).start()

def sync_data():
    log("Sync Data button clicked.")
    if not api_key:
        messagebox.showerror("Error", "API Key not set. Please enter or scan API Key first.")
        log("API Key not set. Sync aborted.")
        return

    status_label.config(text="Connecting to Tally...", fg="#2e7d32")
    progress.start(10)
    app.update_idletasks()

    if not test_tally_connection():
        messagebox.showerror("Error", "Tally not connected. Please open Tally and load the company.")
        status_label.config(text="Tally not connected.", fg="#d32f2f")
        progress.stop()
        log("Tally not connected. Sync aborted.")
        return

    status_label.config(text="Fetching data from Tally...", fg="#2e7d32")
    app.update_idletasks()
    log("Tally connected. Fetching data...")

    all_data = fetch_tally_data()
    if all_data and all_data.get("daybook") and all_data.get("ledger"):
        status_label.config(text="Sending data to backend...", fg="#2e7d32")
        app.update_idletasks()
        log("Data fetched from Tally. Sending to backend...")

        success_daybook = send_data_to_backend(api_key, "daybook", all_data["daybook"])
        success_ledger = send_data_to_backend(api_key, "ledger", all_data["ledger"])

        if success_daybook and success_ledger:
            messagebox.showinfo("Success", "Data synced successfully!")
            status_label.config(text="Data synced successfully!", fg="#388e3c")
            log("Data synced to backend successfully.")
        else:
            messagebox.showerror("Error", "Failed to send some data to backend.")
            status_label.config(text="Partial sync. Check logs.", fg="#fbc02d")
            log("Failed to sync some data to backend.")
    else:
        messagebox.showerror("Error", "No data fetched from Tally.")
        status_label.config(text="No data fetched.", fg="#d32f2f")
        log("No data fetched from Tally.")
    progress.stop()

app.mainloop()


