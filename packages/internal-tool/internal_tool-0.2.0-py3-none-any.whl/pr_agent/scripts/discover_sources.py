#!/usr/bin/env python
# scripts/discover_sources.py

from datetime import datetime
from pr_agent.settings import settings
from pr_agent.connectors.gdrive_connector import list_new_items as list_drive_items
from pr_agent.connectors.notion_connector import list_new_items as list_notion_items
from pr_agent.core.metadata_manager import DirectoryMetadataStore, next_document_id

def discover_sources():
    # 1) Open JSON store
    store = DirectoryMetadataStore(settings.METADATA_DIR)

    
    # 2a) Gather existing doc-IDs (for naming new JSONs)
    seen_doc_ids = store.get_all_ids()

    # 2b) Gather existing connector-IDs (so we don’t re-discover the same file/page)
    existing_source_ids = set()
    for doc_id in seen_doc_ids:
        meta = store.read(doc_id)
        if meta and meta.get("source_id"):
            existing_source_ids.add(meta["source_id"])

    # 3) Ask each connector for new items
    drive_items  = list_drive_items(existing_source_ids, settings.GDRIVE_FOLDER_ID)
    #notion_items = list_notion_items(existing_source_ids)

    new_items = []
    for item in drive_items: #+ notion_items:
        # 4a) Skip anything whose connector-ID we already saw
        if item.id in existing_source_ids:
            continue
        new_items.append(item)
        existing_source_ids.add(item.id)

        # 5) Process only truly new items
    for item in new_items:
        doc_id = next_document_id(seen_doc_ids)
        seen_doc_ids.add(doc_id)


        metadata = {
            "source_id":        item.id,
            "Document ID":       doc_id,
            "Source System":     item.source_system,
            "Original Filename": item.name,
            "Format":            item.name.split(".")[-1].upper(),
            "Date Created":      "",  # optional
            "Last Modified":     item.last_modified,
            "Date Received":     datetime.utcnow().isoformat() + "Z",
            "Ingested At":       "",
            "Status":            "Pending",
            "Summary":           "",
            "Embedding File":    "",
            "File URL":         item.url or "",
            "MIME Type":         item.mime_type or "",
        }

        store.upsert(doc_id, metadata)
        print(f"Discovered {item.name} → saved metadata as {doc_id}.json")

    if not (new_items):
        print("No new items found in any source.")

def main():
    discover_sources()

if __name__ == "__main__":
    main()


