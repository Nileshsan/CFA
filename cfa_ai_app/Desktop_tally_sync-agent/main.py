import tkinter as tk
from tkinter import messagebox
from tally_connector import test_tally_connection, fetch_tally_data
from api_connector import send_data_to_backend
from dotenv import load_dotenv
import os

load_dotenv()

API_KEY = os.getenv("API_KEY")
BACKEND_URL = os.getenv("BACKEND_URL")

if not API_KEY or not BACKEND_URL:
    print("❌ API Key or Backend URL not set in .env file.")
    exit()

def sync_data():
    status_label.config(text="Connecting to Tally...", fg="blue")
    app.update_idletasks()

    if not test_tally_connection():
        messagebox.showerror("Error", "Tally not connected. Please open Tally and load the company.")
        status_label.config(text="Tally not connected.", fg="red")
        return

    status_label.config(text="Fetching data from Tally...", fg="blue")
    app.update_idletasks()

    data = fetch_tally_data()
    if data:
        status_label.config(text="Sending data to backend...", fg="blue")
        app.update_idletasks()

        success = send_data_to_backend("daybook", data)  # You can update "daybook" to correct type

        if success:
            messagebox.showinfo("Success", "Data synced successfully!")
            status_label.config(text="Data synced successfully!", fg="green")
        else:
            messagebox.showerror("Error", "Failed to send data to backend.")
            status_label.config(text="Failed to send data.", fg="red")
    else:
        messagebox.showerror("Error", "No data fetched from Tally.")
        status_label.config(text="No data fetched.", fg="red")

# GUI Setup
app = tk.Tk()
app.title("CFA Tally Sync Agent")
app.geometry("400x250")

tk.Label(app, text="CFA Tally Sync Agent", font=("Arial", 16)).pack(pady=20)

sync_button = tk.Button(app, text="Sync Data Now", command=sync_data, height=2, width=20)
sync_button.pack(pady=10)

status_label = tk.Label(app, text="", font=("Arial", 12))
status_label.pack(pady=20)

app.mainloop()
