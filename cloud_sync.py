
import os
import sys
from pathlib import Path
from pydrive2.auth import GoogleAuth
from pydrive2.drive import GoogleDrive

def get_client_secrets_path():
    base_path = os.path.dirname(sys.executable if hasattr(sys, '_MEIPASS') else __file__)
    path = os.path.join(base_path, "client_secrets.json")
    if not os.path.exists(path):
        raise FileNotFoundError("client_secrets.json not found in application directory")
    return path

def authenticate():
    gauth = GoogleAuth()
    gauth.LoadClientConfigFile(get_client_secrets_path())
    gauth.LocalWebserverAuth()
    return GoogleDrive(gauth)

def upload_to_drive(local_path, remote_filename):
    drive = authenticate()
    remote_title = Path(remote_filename).name
    file_list = drive.ListFile({'q': f"title='{remote_title}' and trashed=false"}).GetList()
    if file_list:
        file = file_list[0]
        file.SetContentFile(local_path)
        file['title'] = remote_title
    else:
        file = drive.CreateFile({'title': remote_title, 'parents': [{'id': 'root'}]})
        file.SetContentFile(local_path)
    file.Upload()
    print(f"{remote_title} uploaded to Google Drive.")

def download_from_drive(remote_filename, local_path):
    drive = authenticate()
    remote_title = Path(remote_filename).name
    file_list = drive.ListFile({'q': f"title='{remote_title}' and trashed=false"}).GetList()
    if file_list:
        file = file_list[0]
        file.GetContentFile(local_path)
        print(f"{remote_title} downloaded to {local_path}.")
        return True
    else:
        print("No backup found.")
        return False
