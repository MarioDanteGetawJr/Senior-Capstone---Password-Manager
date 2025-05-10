"""
cloud_sync.py
Google Drive backup / restore helpers for the Password Manager.

Changes in this version
-----------------------
* Adds a module-level singleton (`_drive`) so OAuth happens **only once
  per application session**.
* Exposes `get_authenticated_drive()` so other modules can re-use
  the same Drive object if they like.
* `upload_to_drive()` and `download_from_drive()` accept an optional
  `drive` parameter but default to the cached singleton, so existing
  calls work unchanged.
"""

from __future__ import annotations

import os
import sys
from pathlib import Path
from typing import Optional

from pydrive2.auth import GoogleAuth
from pydrive2.drive import GoogleDrive

# ───────────────────────────────────────────────────────────────────────────────
# Private helpers / singletons
# ───────────────────────────────────────────────────────────────────────────────

_drive: Optional[GoogleDrive] = None   # keeps the token in memory for this run


def get_client_secrets_path() -> str:
    """
    Locate client_secrets.json regardless of whether the app is frozen
    with PyInstaller or run from source.
    """
    base = (
        sys._MEIPASS  # type: ignore[attr-defined]  # PyInstaller temp dir
        if hasattr(sys, "_MEIPASS")
        else os.path.dirname(__file__)
    )
    path = os.path.join(base, "client_secrets.json")
    if not os.path.exists(path):
        raise FileNotFoundError("client_secrets.json not found in application directory")
    return path


def _authenticate() -> GoogleDrive:
    """Launch the OAuth flow and return an authenticated GoogleDrive object."""
    gauth = GoogleAuth()
    gauth.LoadClientConfigFile(get_client_secrets_path())
    # Will open the browser the first time only
    gauth.LocalWebserverAuth()
    return GoogleDrive(gauth)


def get_authenticated_drive() -> GoogleDrive:
    """
    Return a cached GoogleDrive object, creating it on first use so the
    user is asked to log in only once per program run.
    """
    global _drive
    if _drive is None:
        _drive = _authenticate()
    return _drive


# ───────────────────────────────────────────────────────────────────────────────
# Public API
# ───────────────────────────────────────────────────────────────────────────────


def upload_to_drive(
    local_path: str,
    remote_filename: str,
    drive: Optional[GoogleDrive] = None,
) -> None:
    """
    Upload *local_path* to Google Drive (root). If a file with the same
    title already exists, it is updated in place.

    Parameters
    ----------
    local_path : str
        Path to the file on disk.
    remote_filename : str
        Desired title on Google Drive.
    drive : GoogleDrive, optional
        Pre-authenticated Drive object; if omitted, the cached singleton
        will be used.
    """
    drive = drive or get_authenticated_drive()
    remote_title = Path(remote_filename).name
    query = f"title='{remote_title}' and trashed=false"
    file_list = drive.ListFile({"q": query}).GetList()

    if file_list:
        file_handle = file_list[0]
        file_handle.SetContentFile(local_path)
    else:
        file_handle = drive.CreateFile({"title": remote_title, "parents": [{"id": "root"}]})
        file_handle.SetContentFile(local_path)

    file_handle.Upload()
    print(f"{remote_title} uploaded to Google Drive.")


def download_from_drive(
    remote_filename: str,
    local_path: str,
    drive: Optional[GoogleDrive] = None,
) -> bool:
    """
    Download *remote_filename* from Google Drive into *local_path*.

    Returns
    -------
    bool
        ``True`` if the file existed and was downloaded, ``False`` otherwise.
    """
    drive = drive or get_authenticated_drive()
    remote_title = Path(remote_filename).name
    query = f"title='{remote_title}' and trashed=false"
    file_list = drive.ListFile({"q": query}).GetList()

    if file_list:
        file_list[0].GetContentFile(local_path)
        print(f"{remote_title} downloaded to {local_path}.")
        return True

    print("No backup found on Drive.")
    return False
