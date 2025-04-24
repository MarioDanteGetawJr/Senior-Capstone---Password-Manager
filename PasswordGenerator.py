from Encryption import load_key, encrypt_password, decrypt_password
from cloud_sync import upload_to_drive, download_from_drive

import tkinter as tk
from tkinter import messagebox, Toplevel, simpledialog
import json
import os
import random
import string
import re
import pyotp
import qrcode
from PIL import Image, ImageTk
import io

# Load the encryption key
key = load_key()

def check_pass_strength(password):
    if(len(password) > 8):
        if (re.search(r"\d", password) is not None):
            if (re.search(r"[A-Z]", password) is not None):
                if (re.search(r"[a-z]", password) is not None):
                    if (re.search(r"\W", password) is not None):
                        return "pass"
    messagebox.showwarning("Password strength is too low", "Your password must be at least 8 characters long and must have 1 number, 1 upper case letter, 1 lower case letter, and one special character")
    return "fail"

def on_closing():
    sign_in_window.destroy()
    window.destroy()

def show_new_user_window():
    new_user_window = Toplevel(sign_in_window)
    new_user_window.title("New User Setup")
    new_user_window.geometry("400x550")

    instructions = (
        "To use two-factor authentication (2FA):\n\n"
        "1. After creating your account, a QR code will be displayed below.\n"
        "2. Open your authenticator app (like Google Authenticator).\n"
        "3. Tap 'Add Account' → 'Scan QR Code' and scan the code.\n"
        "4. Use the 6-digit code shown in the app each time you sign in.\n"
    )
    tk.Label(new_user_window, text=instructions, wraplength=380, justify="left").pack(pady=10)

    tk.Label(new_user_window, text="New Account Username:").pack()
    new_username_entry = tk.Entry(new_user_window, width=30)
    new_username_entry.pack()

    tk.Label(new_user_window, text="New Account Password:").pack()
    new_password_entry = tk.Entry(new_user_window, width=30)
    new_password_entry.pack()

    def handle_create():
        username = new_username_entry.get()
        password = new_password_entry.get()

        if check_pass_strength(password) == "pass":
            if username and password:
                secret = pyotp.random_base32()
                totp = pyotp.TOTP(secret)
                uri = totp.provisioning_uri(name=username, issuer_name="PassManager")

                qr_img = qrcode.make(uri)
                buffered = io.BytesIO()
                qr_img.save(buffered, format="PNG")
                qr_data = buffered.getvalue()
                qr_photo = ImageTk.PhotoImage(Image.open(io.BytesIO(qr_data)))

                qr_label = tk.Label(new_user_window, image=qr_photo)
                qr_label.image = qr_photo
                qr_label.pack(pady=10)

                data = {username: {"password": password, "secret": secret}}
                if os.path.exists("passManagerAccounts.json"):
                    with open("passManagerAccounts.json", "r") as file:
                        account_data = json.load(file)
                        account_data.update(data)
                else:
                    account_data = data
                with open("passManagerAccounts.json", "w") as file:
                    json.dump(account_data, file, indent=4)

                messagebox.showinfo("Success", "Account created! Scan the QR code with your authenticator app.")

                def finish_setup():
                    master_username_entry.delete(0, tk.END)
                    master_password_entry.delete(0, tk.END)
                    new_user_window.destroy()
                    window.deiconify()
                    sign_in_window.withdraw()

                tk.Button(new_user_window, text="Continue to App", command=finish_setup).pack(pady=10)
            else:
                messagebox.showwarning("Input Error", "All fields are required.")

    tk.Button(new_user_window, text="Create New Account", command=handle_create).pack(pady=15)

def sign_in():
    account_username = master_username_entry.get()
    account_password = master_password_entry.get()
    file_path = "passwords_" + account_username + ".json"

    not_valid = True
    if os.path.exists("passManagerAccounts.json"):
        with open("passManagerAccounts.json", "r") as file:
            account_data = json.load(file)
            for username, info in account_data.items():
                if username == account_username and info["password"] == account_password:
                    user_secret = info["secret"]
                    totp = pyotp.TOTP(user_secret)
                    code = simpledialog.askstring("2FA Code", "Enter the 6-digit code from your authenticator app:")
                    if not code or not totp.verify(code):
                        messagebox.showwarning("2FA Failed", "Invalid 2FA code.")
                        return

                    if not os.path.exists(file_path):
                        restore = messagebox.askyesno("Restore?", "No local password file found. Restore from Google Drive?")
                        if restore:
                            success = download_from_drive(file_path, file_path)
                            if not success:
                                messagebox.showwarning("Restore Failed", "No backup found on Google Drive.")

                    window.deiconify()
                    sign_in_window.withdraw()
                    not_valid = False
            if not_valid:
                messagebox.showwarning("Invalid Account", "Account does not exist, click Sign Up to create one with the current credentials.")
    else:
        messagebox.showwarning("Invalid Account", "Account does not exist, click Sign Up to create one with the current credentials.")
    master_password_entry.delete(0, tk.END)

def generate_password(length=12):
    characters = string.ascii_letters + string.digits + string.punctuation
    password = "".join(random.choice(characters) for _ in range(length))
    password_entry.delete(0, tk.END)
    password_entry.insert(0, password)

def save_password():
    website = website_entry.get()
    username = username_entry.get()
    account_username = master_username_entry.get()
    password = password_entry.get()
    encrypted_pw = encrypt_password(password, key)

    if check_pass_strength(password) == "pass":
        if website and username and password:
            data = {website: {"username": username, "password": encrypted_pw}}
            file_path = "passwords_" + account_username + ".json"
            if os.path.exists(file_path):
                try:
                    with open(file_path, "r") as file:
                        existing_data = json.load(file)
                except json.JSONDecodeError:
                    existing_data = {}
                existing_data.update(data)
            else:
                existing_data = data

            with open(file_path, "w") as file:
                json.dump(existing_data, file, indent=4)

            try:
                upload_to_drive(file_path, file_path)
                messagebox.showinfo("Cloud Backup", "✅ Cloud backup was successful.")
            except Exception as e:
                messagebox.showwarning("Cloud Backup Failed", f"❌ Cloud backup failed.\n{str(e)}")

            messagebox.showinfo("Success", "Password saved successfully!")
            website_entry.delete(0, tk.END)
            username_entry.delete(0, tk.END)
            password_entry.delete(0, tk.END)
        else:
            messagebox.showwarning("Input Error", "All fields are required.")

def copy_to_clipboard(password):
    window.clipboard_clear()
    window.clipboard_append(password)
    window.update()
    messagebox.showinfo("Copied", "Password copied to clipboard!")

def view_passwords():
    account_username = master_username_entry.get()
    file_path = "passwords_" + account_username + ".json"

    if not os.path.exists(file_path):
        messagebox.showwarning("No Data", "No passwords saved yet.")
        return

    with open(file_path, "r") as file:
        saved_data = json.load(file)

    if not saved_data:
        messagebox.showwarning("No Data", "No passwords available.")
        return

    view_window = Toplevel(window)
    view_window.title("Saved Passwords")
    view_window.geometry("400x400")

    tk.Label(view_window, text="Saved Passwords", font=("Arial", 14, "bold")).pack(pady=5)

    for website, credentials in saved_data.items():
        try:
            decrypted_pw = decrypt_password(credentials["password"], key)
        except Exception:
            decrypted_pw = "Error decrypting"

        display_text = f"Website: {website}\nUsername: {credentials['username']}\nPassword: {decrypted_pw}"
        label = tk.Label(view_window, text=display_text, justify="left", font=("Arial", 10))
        label.pack(pady=5)

        copy_btn = tk.Button(view_window, text="Copy Password", command=lambda pw=decrypted_pw: copy_to_clipboard(pw))
        copy_btn.pack(pady=2)

    tk.Button(view_window, text="Close", command=view_window.destroy).pack(pady=10)

# GUI setup
sign_in_window = tk.Tk()
sign_in_window.title("Sign In")
sign_in_window.geometry("400x400")
sign_in_window.protocol("WM_DELETE_WINDOW", on_closing)

tk.Label(sign_in_window, text="Username:").pack()
master_username_entry = tk.Entry(sign_in_window, width=30)
master_username_entry.pack()

tk.Label(sign_in_window, text="Password:").pack()
master_password_entry = tk.Entry(sign_in_window, width=30)
master_password_entry.pack()

tk.Button(sign_in_window, text="New User?", command=show_new_user_window).pack(pady=5)
tk.Button(sign_in_window, text="Sign In", command=sign_in).pack(pady=5)

window = tk.Tk()
window.title("Password Manager")
window.geometry("400x400")
window.protocol("WM_DELETE_WINDOW", on_closing)

tk.Label(window, text="Website:").pack()
website_entry = tk.Entry(window, width=30)
website_entry.pack()

tk.Label(window, text="Username/Email:").pack()
username_entry = tk.Entry(window, width=30)
username_entry.pack()

tk.Label(window, text="Password:").pack()
password_entry = tk.Entry(window, show="*", width=30)
password_entry.pack()

tk.Button(window, text="Save Password", command=save_password).pack(pady=5)
tk.Button(window, text="Generate Password", command=generate_password).pack(pady=5)
tk.Button(window, text="View Saved Passwords", command=view_passwords).pack(pady=5)

window.withdraw()
window.mainloop()
