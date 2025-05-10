import os, sys, json, random, string, re
import tkinter as tk
from tkinter import messagebox, Toplevel, simpledialog
from PIL import Image, ImageTk
import qrcode, pyotp

# ─── run-from-EXE convenience ────────────────────────────────────────────────
# When frozen with PyInstaller, switch the working directory to the folder
# that holds PasswordManager.exe so every file we create lands beside it.
if getattr(sys, "frozen", False):
    os.chdir(os.path.dirname(sys.executable))

# ─── local modules ───────────────────────────────────────────────────────────
from Encryption import load_key, encrypt_password, decrypt_password
from cloud_sync import upload_to_drive, download_from_drive, get_authenticated_drive

# ─── globals ─────────────────────────────────────────────────────────────────
cloud_drive = None                    # reused Google Drive handle this session

def local_path(fname: str) -> str:
    """
    Persistent, writable path for *fname*:
    • Frozen app → same folder as the .exe
    • Dev run    → current working directory
    """
    base = os.path.dirname(sys.executable) if getattr(sys, "frozen", False) else os.path.abspath(".")
    return os.path.join(base, fname)

# ─── helpers ─────────────────────────────────────────────────────────────────
def check_pass_strength(pw: str) -> str:
    if (len(pw) >= 8 and
        re.search(r"\d", pw) and
        re.search(r"[A-Z]", pw) and
        re.search(r"[a-z]", pw) and
        re.search(r"\W", pw)):
        return "pass"
    messagebox.showwarning(
        "Weak Password",
        "Password must be 8+ chars and include upper/lowercase letters, a number, and a symbol."
    )
    return "fail"

def copy_to_clipboard(text: str) -> None:
    window.clipboard_clear()
    window.clipboard_append(text)
    window.update()
    messagebox.showinfo("Copied", "Password copied to clipboard.")

def on_closing():
    sign_in_window.destroy()
    window.destroy()

# ─── new-user flow ───────────────────────────────────────────────────────────
def show_new_user_window():
    new_user_window = Toplevel(sign_in_window)
    new_user_window.title("New User Setup")
    new_user_window.geometry("500x650")

    instructions = (
        "To use two-factor authentication (2FA):\n\n"
        "1. After creating your account, a QR code will be displayed below.\n"
        "2. Open your authenticator app (Google Authenticator, Authy, etc.).\n"
        "3. Tap 'Add Account' → 'Scan QR Code' and scan the code.\n"
        "4. Use the 6-digit code shown in the app each time you sign in."
    )
    tk.Label(new_user_window, text=instructions, justify="left",
             anchor="w", wraplength=480).pack(padx=10, pady=(10, 20))

    tk.Label(new_user_window, text="New Account Username:").pack()
    new_username_entry = tk.Entry(new_user_window, width=40)
    new_username_entry.pack()

    tk.Label(new_user_window, text="New Account Password:").pack(pady=(10, 0))
    new_password_entry = tk.Entry(new_user_window, width=40, show="*")
    new_password_entry.pack()

    # ── handler ──────────────────────────────────────────────────────────────
    def handle_create():
        global cloud_drive
        username = new_username_entry.get().strip()
        password = new_password_entry.get().strip()
        if not username or not password or check_pass_strength(password) != "pass":
            return

        # TOTP secret + larger QR (box_size 10 ≈360 px) fits window fully
        secret = pyotp.random_base32()
        uri = pyotp.TOTP(secret).provisioning_uri(name=username, issuer_name="PassManager")
        qr = qrcode.QRCode(box_size=8, border=4)
        qr.add_data(uri); qr.make(fit=True)
        qr_img   = qr.make_image(fill_color="black", back_color="white").convert("RGB")
        qr_photo = ImageTk.PhotoImage(qr_img)
        qr_lbl   = tk.Label(new_user_window, image=qr_photo)
        qr_lbl.pack(pady=15)
        new_user_window.qr_photo = qr_photo       # keep reference

        # save account locally
        key = load_key()
        enc_pw = encrypt_password(password, key)
        acct_path = local_path("passManagerAccounts.json")
        data = {}
        if os.path.exists(acct_path):
            with open(acct_path, "r") as f: data = json.load(f)
        data[username] = {"password": enc_pw, "secret": secret}
        with open(acct_path, "w") as f: json.dump(data, f, indent=4)

        # create empty user passwords file
        pw_file = local_path(f"passwords_{username}.json")
        if not os.path.exists(pw_file):
            with open(pw_file, "w") as f: json.dump({}, f)

        # optional initial backup
        if messagebox.askyesno("Enable Cloud Backup?",
                               "Back up your account to Google Drive now?"):
            cloud_drive = cloud_drive or get_authenticated_drive()
            upload_to_drive(acct_path, "passManagerAccounts.json", cloud_drive)
            upload_to_drive(pw_file,  f"passwords_{username}.json", cloud_drive)
            upload_to_drive(local_path("password_manager.key"), "password_manager.key", cloud_drive)

        messagebox.showinfo(
            "Account Created",
            "Account created.\nSign in with your credentials and 6-digit code."
        )

    tk.Button(new_user_window, text="Create New Account",
              command=handle_create).pack(pady=25)

# ─── sign-in flow ────────────────────────────────────────────────────────────
def sign_in():
    global cloud_drive
    uname = master_username_entry.get().strip()
    pw    = master_password_entry.get().strip()
    acct_path = local_path("passManagerAccounts.json")
    pw_file   = local_path(f"passwords_{uname}.json")

    # restore missing files
    if not os.path.exists(acct_path) and \
       messagebox.askyesno("Restore?", "No local account file found. Restore from cloud?"):
        cloud_drive = cloud_drive or get_authenticated_drive()
        download_from_drive("passManagerAccounts.json", acct_path, cloud_drive)

    if not os.path.exists(local_path("password_manager.key")) and \
       messagebox.askyesno("Restore?", "Key file missing. Restore from cloud?"):
        cloud_drive = cloud_drive or get_authenticated_drive()
        download_from_drive("password_manager.key", local_path("password_manager.key"), cloud_drive)
    key = load_key()

    try:
        with open(acct_path, "r") as f: accts = json.load(f)
        decrypted = decrypt_password(accts[uname]["password"], key)
        if decrypted != pw:
            raise ValueError
    except Exception:
        messagebox.showwarning("Login Failed", "Invalid username or password.")
        return

    # MFA
    totp = pyotp.TOTP(accts[uname]["secret"])
    code = simpledialog.askstring("2FA Code", "Enter the 6-digit code:")
    if not code or not totp.verify(code):
        messagebox.showwarning("2FA Failed", "Invalid 2-factor code.")
        return

    # optional restore of user passwords file
    if not os.path.exists(pw_file) and \
       messagebox.askyesno("Restore?", "No password file found. Restore from cloud?"):
        cloud_drive = cloud_drive or get_authenticated_drive()
        download_from_drive(f"passwords_{uname}.json", pw_file, cloud_drive)

    window.deiconify(); sign_in_window.withdraw()

# ─── password actions ────────────────────────────────────────────────────────
def generate_password(length: int = 12):
    chars = string.ascii_letters + string.digits + string.punctuation
    password_entry.delete(0, tk.END)
    password_entry.insert(0, ''.join(random.choice(chars) for _ in range(length)))

def save_password():
    site  = website_entry.get().strip()
    user  = username_entry.get().strip()
    pw    = password_entry.get().strip()
    owner = master_username_entry.get().strip()
    if not (site and user and pw) or check_pass_strength(pw) != "pass":
        return
    key = load_key()
    enc_pw = encrypt_password(pw, key)
    pw_file = local_path(f"passwords_{owner}.json")
    data = {}
    if os.path.exists(pw_file):
        with open(pw_file, "r") as f: data = json.load(f)
    data[site] = {"username": user, "password": enc_pw}
    with open(pw_file, "w") as f: json.dump(data, f, indent=4)
    messagebox.showinfo("Saved", "Password saved.")
    website_entry.delete(0, tk.END); username_entry.delete(0, tk.END); password_entry.delete(0, tk.END)

def view_passwords():
    owner = master_username_entry.get().strip()
    pw_file = local_path(f"passwords_{owner}.json")
    if not os.path.exists(pw_file):
        messagebox.showwarning("No Data", "No passwords saved yet."); return
    with open(pw_file, "r") as f: data = json.load(f)
    if not data:
        messagebox.showwarning("No Data", "No passwords saved yet."); return
    vw = Toplevel(window); vw.title("Saved Passwords"); vw.geometry("400x400")
    key = load_key()
    for site, cred in data.items():
        try: dec = decrypt_password(cred["password"], key)
        except: dec = "Error decrypting"
        tk.Label(vw, text=f"Website: {site}\nUsername: {cred['username']}\nPassword: {dec}",
                 justify="left").pack(pady=4)
        tk.Button(vw, text="Copy", command=lambda p=dec: copy_to_clipboard(p)).pack()

def save_to_cloud():
    global cloud_drive
    owner = master_username_entry.get().strip()
    acct_path = local_path("passManagerAccounts.json")
    pw_file   = local_path(f"passwords_{owner}.json")
    key_file  = local_path("password_manager.key")
    if not os.path.exists(pw_file):
        messagebox.showwarning("No File", "No password file to upload."); return
    try:
        cloud_drive = cloud_drive or get_authenticated_drive()
        upload_to_drive(acct_path, "passManagerAccounts.json", cloud_drive)
        upload_to_drive(pw_file,   f"passwords_{owner}.json", cloud_drive)
        upload_to_drive(key_file,  "password_manager.key",     cloud_drive)
        messagebox.showinfo("Uploaded", "Files backed up to cloud.")
    except Exception as e:
        messagebox.showwarning("Backup Failed", str(e))

# ─── GUI ─────────────────────────────────────────────────────────────────────
sign_in_window = tk.Tk(); sign_in_window.title("Sign In"); sign_in_window.geometry("400x400")
sign_in_window.protocol("WM_DELETE_WINDOW", on_closing)
tk.Label(sign_in_window, text="Username:").pack()
master_username_entry = tk.Entry(sign_in_window, width=30); master_username_entry.pack()
tk.Label(sign_in_window, text="Password:").pack()
master_password_entry = tk.Entry(sign_in_window, width=30, show="*"); master_password_entry.pack()
tk.Button(sign_in_window, text="New User?", command=show_new_user_window).pack(pady=5)
tk.Button(sign_in_window, text="Sign In", command=sign_in).pack(pady=5)

window = tk.Toplevel(); window.withdraw(); window.title("Password Manager"); window.geometry("400x400")
window.protocol("WM_DELETE_WINDOW", on_closing)
tk.Label(window, text="Website:").pack()
website_entry = tk.Entry(window, width=30); website_entry.pack()
tk.Label(window, text="Username/Email:").pack()
username_entry = tk.Entry(window, width=30); username_entry.pack()
tk.Label(window, text="Password:").pack()
password_entry = tk.Entry(window, width=30, show="*"); password_entry.pack()
tk.Button(window, text="Save Password",           command=save_password).pack(pady=5)
tk.Button(window, text="Generate Password",       command=generate_password).pack(pady=5)
tk.Button(window, text="View Saved Passwords",    command=view_passwords).pack(pady=5)
tk.Button(window, text="Upload Passwords to Cloud", command=save_to_cloud).pack(pady=5)

window.mainloop()
