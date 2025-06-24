import os
import sys

# DLL path fix for PyInstaller
if getattr(sys, 'frozen', False):
    base_path = sys._MEIPASS
else:
    base_path = os.path.abspath(".")

os.environ['PATH'] += os.pathsep + base_path

# Imports
import tkinter as tk
from tkinter import messagebox
from tally_connector import test_tally_connection, fetch_tally_data
from api_connector import send_data_to_backend
from dotenv import load_dotenv
import cv2

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
                found = True

        cv2.imshow("Scan QR Code (Press Q to exit)", frame)
        if cv2.waitKey(1) & 0xFF == ord('q'):
            break

    cap.release()
    cv2.destroyAllWindows()

def sync_data():
    if not api_key:
        messagebox.showerror("Error", "API Key not set. Please enter or scan API Key first.")
        return

    status_label.config(text="Connecting to Tally...", fg="blue")
    app.update_idletasks()

    if not test_tally_connection():
        messagebox.showerror("Error", "Tally not connected. Please open Tally and load the company.")
        status_label.config(text="Tally not connected.", fg="red")
        return

    status_label.config(text="Fetching data from Tally...", fg="blue")
    app.update_idletasks()

    all_data = fetch_tally_data()
    if all_data["daybook"] and all_data["ledger"]:
        status_label.config(text="Sending data to backend...", fg="blue")
        app.update_idletasks()

        success_daybook = send_data_to_backend(api_key, "daybook", all_data["daybook"])
        success_ledger = send_data_to_backend(api_key, "ledger", all_data["ledger"])

        if success_daybook and success_ledger:
            messagebox.showinfo("Success", "Data synced successfully!")
            status_label.config(text="Data synced successfully!", fg="green")
        else:
            messagebox.showerror("Error", "Failed to send some data to backend.")
            status_label.config(text="Partial sync. Check logs.", fg="orange")
    else:
        messagebox.showerror("Error", "No data fetched from Tally.")
        status_label.config(text="No data fetched.", fg="red")

# GUI Setup
app = tk.Tk()
app.title("CFA Tally Sync Agent")
app.geometry("450x350")

tk.Label(app, text="CFA Tally Sync Agent", font=("Arial", 16)).pack(pady=10)

# API Key Input
tk.Label(app, text="Enter API Key:", font=("Arial", 12)).pack(pady=5)
api_entry = tk.Entry(app, width=40)
api_entry.pack(pady=5)
api_entry.insert(0, api_key)

tk.Button(app, text="Save API Key", command=update_api_key, height=1, width=15).pack(pady=5)
tk.Button(app, text="Scan API Key QR", command=scan_qr, height=1, width=15).pack(pady=5)
tk.Button(app, text="Sync Data Now", command=sync_data, height=2, width=20).pack(pady=20)

status_label = tk.Label(app, text="", font=("Arial", 12))
status_label.pack(pady=10)

app.mainloop()
