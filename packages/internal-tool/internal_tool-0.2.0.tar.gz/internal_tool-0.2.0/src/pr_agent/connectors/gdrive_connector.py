# pr_agent/connectors/gdrive_connector.py

from typing import List, Set
from pr_agent.drive_client import get_drive_service
from pr_agent.drive_client import list_files_in_folder
from pr_agent.connectors.base_connector import SourceItem
from pr_agent.drive_client import get_drive_service, list_files_in_folder
from pr_agent.drive_client import download_file_bytes

def _gather_all_files_recursively(folder_id: str) -> List[dict]:
    """
    Returns a flat list of file‐metadata dicts for every non‐folder item under `folder_id`,
    descending into subfolders recursively.
    Each dict has keys: { 'id': fileId, 'name': fileName, 'modifiedTime': ... }.
    """
    all_files = []
    # 1) List everything directly in this folder
    results = list_files_in_folder(folder_id)
    #print(f"\nContents of folder {folder_id}:") # <- debug

    for meta in results:
        #print("  •", meta["name"], "→", meta["mimeType"])  # <— debug
        file_id   = meta["id"]
        name      = meta["name"]
        mime_type = meta.get("mimeType", "")

        if mime_type == "application/vnd.google-apps.folder":
            # Found a subfolder: recurse into it
            subfolder_id = file_id
            nested = _gather_all_files_recursively(subfolder_id)
            all_files.extend(nested)
        else:
            # It’s a normal file (PDF, DOCX, TXT, etc.)
            all_files.append(meta)

    return all_files


def list_new_items(existing_ids: Set[str], root_folder_id: str) -> List[SourceItem]:
    """
    Now uses a recursive gather to find every file under root_folder_id (any depth).
    """

    #service = get_drive_service()

    # Request webViewLink so we get the exact UI URL Drive shows
    # results = service.files().list(
    #     q=query,
    #     pageSize=1000,
    #     fields=(
    #         "nextPageToken, "
    #         "files(id, name, modifiedTime, mimeType, webViewLink)"
    #     )
    # ).execute()

    # 1) Recursively gather all file-metadata dicts under root_folder_id
    all_file_meta = _gather_all_files_recursively(root_folder_id)

    items: List[SourceItem] = []

    for meta in all_file_meta:
        file_id   = meta["id"]
        if file_id in existing_ids:
             continue
        mime_type = meta.get("mimeType", "")
        filename  = meta["name"]
        # if this was a Google-Doc, we just grabbed it as PDF:
        if mime_type == "application/vnd.google-apps.document":
            filename += ".pdf"
        modified  = meta.get("modifiedTime", "")
        web_url    = meta.get("webViewLink")
        if not web_url:
            web_url = f"https://drive.google.com/file/d/{file_id}/view"

        # Fallback for any odd cases where webViewLink is missing:
        # if not web_url:
        #     # Native Google Docs
        #     if mime_type == "application/vnd.google-apps.document":
        #         web_url = f"https://docs.google.com/document/d/{file_id}/edit"
        #     # Google Sheets
        #     elif mime_type == "application/vnd.google-apps.spreadsheet":
        #         web_url = f"https://docs.google.com/spreadsheets/d/{file_id}/edit"
        #     # All other binaries
        #     else:
        #         web_url = f"https://drive.google.com/file/d/{file_id}/view"



        # 3) Download the file’s bytes
        #buffer = fetch_file_bytes(file_id)  # BytesIO

        # 3) Download the file’s bytes (exports Google-native if needed)
        buffer = download_file_bytes(file_id, mime_type)

        # 4) Wrap into a SourceItem
        item = SourceItem(
            id=file_id,
            name=filename,
            raw_bytes=buffer,
            last_modified=modified,
            source_system="GoogleDrive",
            url=web_url,
            mime_type=mime_type
        )
        items.append(item)

    return items
