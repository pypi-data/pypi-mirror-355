# pr_agent/drive_client.py

import io
from google.oauth2 import service_account
from googleapiclient.discovery import build
from googleapiclient.http import MediaIoBaseDownload
#from pr_agent.settings import GDRIVE_CREDFILE, GDRIVE_SCOPES

from pr_agent.settings import settings  

credfile = settings.GDRIVE_CRED_FILE
gdrive_scope = settings.GDRIVE_SCOPES

def get_drive_service():
    """
    Returns an authenticated Drive API client (service account).
    """
    creds = service_account.Credentials.from_service_account_file(
        credfile, scopes=gdrive_scope
    )
    return build("drive", "v3", credentials=creds)

def list_files_in_folder(folder_id: str):
    """
    List all non‐folder files in the given Drive folder ID.
    Returns: a list of dicts, each { "id": fileId, "name": fileName, "modifiedTime": RFC3339 }.
    """
    service = get_drive_service()
    results = []
    page_token = None
    allowed_mime_types = [
    "application/vnd.google-apps.document",  # Google Docs
    "application/pdf",                       # PDFs
    "application/vnd.openxmlformats-officedocument.wordprocessingml.document", # DOCX
    "text/plain" # TXT
    "application/vnd.openxmlformats-officedocument.spreadsheetml.sheet", # XLSX
    "text/csv",
    "text/markdown"
    ]

    mime_filters = " or ".join([f"mimeType = '{mime}'" for mime in allowed_mime_types])
    query = f"('{folder_id}' in parents) and trashed = false and ({mime_filters})"

    # query = f"'{folder_id}' in parents and trashed = false"
    while True:
        resp = service.files().list(
            q=query,
            corpora="allDrives",
            includeItemsFromAllDrives=True,
            supportsAllDrives=True,
            spaces="drive",
            fields="nextPageToken, files(id, name, mimeType, modifiedTime, webViewLink)",
            pageToken=page_token
        ).execute()
        results.extend(resp.get("files", []))
        page_token = resp.get("nextPageToken")
        if not page_token:
            break
    return results

def fetch_file_bytes(file_id: str):
    """
    Download a file’s raw bytes from Drive into an in‐memory BytesIO buffer.
    Returns: io.BytesIO positioned at start.
    """
    service = get_drive_service()
    request = service.files().get_media(fileId=file_id)
    buffer = io.BytesIO()
    downloader = MediaIoBaseDownload(buffer, request)
    done = False
    while not done:
        status, done = downloader.next_chunk()
    buffer.seek(0)
    return buffer

def download_file_bytes(file_id: str, mime_type: str) -> io.BytesIO:
    """
    Smart download:
      • For native Google Docs/Sheets/Slides, exports as PDF.
      • Otherwise streams the raw file bytes.
    """
    service = get_drive_service()

    # Decide whether to export as PDF (native Google file)
    # if "docs.google.com/document" in url \
    # or "spreadsheets/d/"      in url \
    # or "presentation/d/"      in url:
    #     # Export to PDF
    #     request = service.files().export_media(
    #         fileId=file_id,
    #         mimeType="application/pdf"
    #     )
    # else:
    #     # Binary or other files
    #     request = service.files().get_media(fileId=file_id)

    # Determine by the stored mime_type, not by URL
    #from pr_agent.settings import settings
    # We assume `url` came from metadata, but actually branch on mime_type:
    #mime_type = settings  # placeholder
    # Instead of URL-based logic, branch on actual MIME Type:
    # (lift mime_type from metadata in the CLI caller)
    # e.g. in your CLI: download_file_bytes(file_id, meta["mime_type"])
    if mime_type and mime_type.startswith("application/vnd.google-apps"):
        request = service.files().export_media(
            fileId=file_id,
            mimeType="application/pdf"
        )
    else:
        request = service.files().get_media(fileId=file_id)

    buffer = io.BytesIO()
    downloader = MediaIoBaseDownload(buffer, request)
    done = False
    while not done:
        status, done = downloader.next_chunk()
    buffer.seek(0)
    return buffer
