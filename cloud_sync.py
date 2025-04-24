from pydrive2.auth import GoogleAuth
from pydrive2.drive import GoogleDrive
def authenticate():
    gauth = GoogleAuth()
    gauth.LocalWebserverAuth()  # Opens a browser window for Google login
    return GoogleDrive(gauth)

def upload_to_drive(local_path, remote_filename):
    drive = authenticate()
    file_list = drive.ListFile({'q': f"title='{remote_filename}'"}).GetList()
    if file_list:
        file = file_list[0]
        file.SetContentFile(local_path)
    else:
        file = drive.CreateFile({'title': remote_filename})
        file.SetContentFile(local_path)
    file.Upload()
    print(f"{remote_filename} uploaded to Google Drive.")

def download_from_drive(remote_filename, local_path):
    drive = authenticate()
    file_list = drive.ListFile({'q': f"title='{remote_filename}'"}).GetList()

    if file_list:
        file = file_list[0]
        file.GetContentFile(local_path)
        print(f"{remote_filename} downloaded to {local_path}.")
        return True
    else:
        print("No backup found.")
        return False
