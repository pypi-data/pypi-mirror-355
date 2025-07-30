# pr_agent/core/json_writer.py

import os
import json

def build_json_payload(metadata_row: dict,
                       summary: str,
                       embedding_path: str) -> dict:
    """
    Constructs a JSON‐serializable payload that reflects exactly your new metadata schema:
      - document_id
      - source_system
      - original_filename
      - format
      - date_created
      - last_modified
      - date_received
      - ingested_at
      - status
      - summary
      - embedding_file_path
    """
    return {
        "source_id":          metadata_row.get("source_id",""),
        "document_id":        metadata_row.get("Document ID", ""),
        "source_system":      metadata_row.get("Source System", ""),
        "original_filename":  metadata_row.get("Original Filename", ""),
        "format":             metadata_row.get("Format", ""),
        "date_created":       metadata_row.get("Date Created", ""),
        "last_modified":      metadata_row.get("Last Modified", ""),
        "date_received":      metadata_row.get("Date Received", ""),
        "ingested_at":        metadata_row.get("Ingested At", ""),
        "status":             metadata_row.get("Status", ""),
        "summary":            summary,
        "embedding_file_path": embedding_path,
        "file_url":            metadata_row.get("File URL", ""),
        "mime_type":            metadata_row.get("MIME Type", ""),
    }

def write_json_file(payload: dict, doc_id: str, output_dir: str) -> str:
    """
    Writes the JSON payload (built above) to disk as `<doc_id>_metadata.json`
    inside output_dir, creating output_dir if necessary.
    """
    os.makedirs(output_dir, exist_ok=True)
    filepath = os.path.join(output_dir, f"{doc_id}.json")
    with open(filepath, "w", encoding="utf-8") as f:
        json.dump(payload, f, indent=2, ensure_ascii=False)
    return filepath
