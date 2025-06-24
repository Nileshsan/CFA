import os
import sys
import tkinter as tk
from tkinter import messagebox
from tally_connector import test_tally_connection, fetch_tally_data
from api_connector import send_data_to_backend
from dotenv import load_dotenv
import cv2
import datetime

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

# GUI Setup
app = tk.Tk()
app.title("CFA Tally Sync Agent")
app.geometry("500x400")
app.configure(bg="#f0f0f0")

tk.Label(app, text="CFA Tally Sync Agent", font=("Arial", 20, "bold"), bg="#f0f0f0", fg="#333").pack(pady=15)

tk.Label(app, text="Enter API Key:", font=("Arial", 12), bg="#f0f0f0").pack(pady=5)
api_entry = tk.Entry(app, width=45, font=("Arial", 12))
api_entry.pack(pady=5)
api_entry.insert(0, api_key)

button_frame = tk.Frame(app, bg="#f0f0f0")
button_frame.pack(pady=10)

tk.Button(button_frame, text="Save API Key", command=lambda: update_api_key(), height=1, width=15, bg="#4CAF50", fg="white").grid(row=0, column=0, padx=10)
tk.Button(button_frame, text="Scan API Key QR", command=lambda: scan_qr(), height=1, width=15, bg="#2196F3", fg="white").grid(row=0, column=1, padx=10)
tk.Button(app, text="Sync Data Now", command=lambda: sync_data(), height=2, width=20, bg="#FF5722", fg="white", font=("Arial", 12, "bold")).pack(pady=20)

status_label = tk.Label(app, text="", font=("Arial", 12), bg="#f0f0f0")
status_label.pack(pady=10)

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
                cv2.line(frame, tuple(bbox[i][0]), tuple(bbox[(i + 1) % len(bbox)][0]), color=(255, 0, 0), thickness=2)

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

def sync_data():
    log("Sync Data button clicked.")
    if not api_key:
        messagebox.showerror("Error", "API Key not set. Please enter or scan API Key first.")
        log("API Key not set. Sync aborted.")
        return

    status_label.config(text="Connecting to Tally...", fg="blue")
    app.update_idletasks()

    if not test_tally_connection():
        messagebox.showerror("Error", "Tally not connected. Please open Tally and load the company.")
        status_label.config(text="Tally not connected.", fg="red")
        log("Tally not connected. Sync aborted.")
        return

    status_label.config(text="Fetching data from Tally...", fg="blue")
    app.update_idletasks()
    log("Tally connected. Fetching data...")

    all_data = fetch_tally_data()
    if all_data and all_data["daybook"] and all_data["ledger"]:
        status_label.config(text="Sending data to backend...", fg="blue")
        app.update_idletasks()
        log("Data fetched from Tally. Sending to backend...")

        success_daybook = send_data_to_backend(api_key, "daybook", all_data["daybook"])
        success_ledger = send_data_to_backend(api_key, "ledger", all_data["ledger"])

        if success_daybook and success_ledger:
            messagebox.showinfo("Success", "Data synced successfully!")
            status_label.config(text="Data synced successfully!", fg="green")
            log("Data synced to backend successfully.")
        else:
            messagebox.showerror("Error", "Failed to send some data to backend.")
            status_label.config(text="Partial sync. Check logs.", fg="orange")
            log("Failed to sync some data to backend.")
    else:
        messagebox.showerror("Error", "No data fetched from Tally.")
        status_label.config(text="No data fetched.", fg="red")
        log("No data fetched from Tally.")

app.mainloop()


