import tkinter as tk
from tkinter import messagebox, Toplevel
import json
import os
import random
import string

def on_closing():
    sign_in_window.destroy()
    window.destroy()

def create_account():
    username = master_username_entry.get()
    password = master_password_entry.get()

    if username and password:
        data = {username: password}
        # data = {username: {"username": username, "password": password}}

        # Save to a local JSON file
        if os.path.exists("passManagerAccounts.json"):
            with open("passManagerAccounts.json", "r") as file:
                account_data = json.load(file)
                account_data.update(data)
        else:
            account_data = data
        with open("passManagerAccounts.json", "w") as file:
            json.dump(account_data, file, indent=4)

        messagebox.showinfo("Success", "Accout Created successfully!")
        window.deiconify()
        master_password_entry.delete(0, tk.END)
        sign_in_window.withdraw()

    else:
        messagebox.showwarning("Input Error", "All fields are required.")

def sign_in():
    account_username = master_username_entry.get()
    account_password = master_password_entry.get()

    not_valid = True
    if os.path.exists("passManagerAccounts.json"):
        with open("passManagerAccounts.json", "r") as file:
            account_data = json.load(file)
            for username, password in account_data.items():
                if username == account_username and password == account_password:
                    window.deiconify()
                    sign_in_window.withdraw()   
                    not_valid = False
            if(not_valid):
                messagebox.showwarning("Invalid Account", "Account does not exist, click Sign Up to create one with the current credentials.")

    else:
        messagebox.showwarning("Invalid Account", "Account does not exist, click Sign Up to create one with the current credentials.")

    master_password_entry.delete(0, tk.END)


# generate a password
def generate_password(length=12):
    #Generates a random password with uppercase, numbers, and special characters.
    characters = string.ascii_letters + string.digits + string.punctuation
    password = "".join(random.choice(characters) for _ in range(length))
    
    # Insert generated password into the password entry field
    password_entry.delete(0, tk.END)
    password_entry.insert(0, password)

# Function to save a password
def save_password():
    website = website_entry.get()
    username = username_entry.get()
    account_username = master_username_entry.get()
    password = password_entry.get()

    if website and username and password:
        data = {website: {"username": username, "password": password}}
        
        # Save to a local JSON file
        if os.path.exists("passwords_" + account_username + ".json"):
            with open("passwords_" + account_username + ".json", "r") as file:
                existing_data = json.load(file)
                existing_data.update(data)
        else:
            existing_data = data

        with open("passwords_" + account_username + ".json", "w") as file:
            json.dump(existing_data, file, indent=4)

        messagebox.showinfo("Success", "Password saved successfully!")
        website_entry.delete(0, tk.END)
        username_entry.delete(0, tk.END)
        password_entry.delete(0, tk.END)
    else:
        messagebox.showwarning("Input Error", "All fields are required.")

# Function to copy a password to clipboard
def copy_to_clipboard(password):
    #Copies the selected password to clipboard.
    window.clipboard_clear()
    window.clipboard_append(password)
    window.update()
    messagebox.showinfo("Copied", "Password copied to clipboard!")

# Function to open a new window and display saved passwords
def view_passwords():
    account_username = master_username_entry.get()
    #Opens a new window to display stored passwords.
    if not os.path.exists("passwords_" + account_username + ".json"):
        messagebox.showwarning("No Data", "No passwords saved yet.")
        return

    with open("passwords_" + account_username + ".json", "r") as file:
        saved_data = json.load(file)

    if not saved_data:
        messagebox.showwarning("No Data", "No passwords available.")
        return

    # Create a new top-level window
    view_window = Toplevel(window)
    view_window.title("Saved Passwords")
    view_window.geometry("400x400")

    tk.Label(view_window, text="Saved Passwords", font=("Arial", 14, "bold")).pack(pady=5)

    for website, credentials in saved_data.items():
        site_label = tk.Label(view_window, text=f"{website} - {credentials['username']}", font=("Arial", 10))
        site_label.pack()

        copy_btn = tk.Button(view_window, text="Copy Password", command=lambda pw=credentials['password']: copy_to_clipboard(pw))
        copy_btn.pack(pady=2)

    tk.Button(view_window, text="Close", command=view_window.destroy).pack(pady=10)

# Initialize main window
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

tk.Button(sign_in_window, text="Create Account", command=create_account).pack(pady=5)
tk.Button(sign_in_window, text="Sign In", command=sign_in).pack(pady=5)

window = tk.Tk()
window.title("Password Manager")
window.geometry("400x400")
window.protocol("WM_DELETE_WINDOW", on_closing)

# GUI Layout
tk.Label(window, text="Website:").pack()
website_entry = tk.Entry(window, width=30)
website_entry.pack()

tk.Label(window, text="Username/Email:").pack()
username_entry = tk.Entry(window, width=30)
username_entry.pack()

tk.Label(window, text="Password:").pack()
password_entry = tk.Entry(window, show="*", width=30)
password_entry.pack()

# Buttons for saving, generating, and viewing passwords
tk.Button(window, text="Save Password", command=save_password).pack(pady=5)
tk.Button(window, text="Generate Password", command=generate_password).pack(pady=5)
tk.Button(window, text="View Saved Passwords", command=view_passwords).pack(pady=5)

window.withdraw()

window.mainloop()
