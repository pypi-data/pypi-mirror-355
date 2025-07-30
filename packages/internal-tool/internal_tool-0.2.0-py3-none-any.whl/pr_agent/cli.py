# src/pr_agent/cli.py

import typer
import requests
from io import BytesIO
from pathlib import Path
from pr_agent.core.metadata_manager import DirectoryMetadataStore
from pr_agent.settings import settings
from pr_agent.drive_client import download_file_bytes

from pr_agent.drive_client import get_drive_service, fetch_file_bytes
from googleapiclient.http import MediaIoBaseDownload

app = typer.Typer(help="PR-Agent CLI: explore your discovered docs")

@app.command("list-docs")
def list_docs():
    """
    List all discovered documents with their doc_id and filename.
    """
    store = DirectoryMetadataStore(settings.METADATA_DIR)
    for doc_id in sorted(store.get_all_ids()):
        meta = store.read(doc_id)
        typer.echo(f"{doc_id}  →  {meta.get('original_filename')}")

@app.command("show-url")
def show_url(doc_id: str):
    """
    Print the Original File URL for a given document ID.
    """
    store = DirectoryMetadataStore(settings.METADATA_DIR)
    meta = store.read(doc_id)
    url = meta.get("file_url")
    if not url:
        typer.secho(f"[!] No URL found for {doc_id}", fg=typer.colors.RED)
        raise typer.Exit(code=1)
    typer.echo(url)

@app.command("download")
def download(
    doc_id: str,
    output_dir: Path = settings.DOWNLOAD_DIR
):
    """
    Download the file for DOC_ID to DOWNLOAD_DIR.
    """
    store   = DirectoryMetadataStore(settings.METADATA_DIR)
    meta    = store.read(doc_id)
    url     = meta.get("file_url")
    name    = meta.get("original_filename") or f"{doc_id}"
    source = meta.get("source_system")
    file_id = meta.get("source_id")
    mime_type = meta.get("mime_type")  

    if not url:
        typer.secho(f"[!] No URL found for {doc_id}", fg=typer.colors.RED)
        raise typer.Exit(code=1)

    output_dir.mkdir(parents=True, exist_ok=True)
    outpath = output_dir / name

    # typer.echo(f"Downloading {doc_id} → {url}")
    # resp = requests.get(url)
    # try:
    #     resp.raise_for_status()
    # except Exception as e:
    #     typer.secho(f"[!] Download failed: {e}", fg=typer.colors.RED)
    #     raise typer.Exit(code=1)

    # with open(outpath, "wb") as f:
    #     f.write(resp.content)

    typer.echo(f"Downloading {doc_id} → {outpath}")

    if source == "GoogleDrive":
        buffer = download_file_bytes(file_id, mime_type)
        with open(outpath, "wb") as f:
            f.write(buffer.getvalue())
    else:
        # e.g. Notion attachments, public URLs
        resp = requests.get(url)
        resp.raise_for_status()
        with open(outpath, "wb") as f:
            f.write(resp.content)

    typer.secho(f"Saved to {outpath}", fg=typer.colors.GREEN)

# def cli_list_docs():
#     """Entry point for the standalone `list-docs` script."""
#     # simply delegate to the Typer command
#     sys.exit(app(["list-docs"]))

# def cli_show_url():
#     """Entry point for the standalone `show-url <doc_id>` script."""
#     if len(sys.argv) != 2:
#         print("Usage: show-url <doc_id>")
#         sys.exit(1)
#     doc_id = sys.argv[1]
#     sys.exit(app(["show-url", doc_id]))


if __name__ == "__main__":
    app()
