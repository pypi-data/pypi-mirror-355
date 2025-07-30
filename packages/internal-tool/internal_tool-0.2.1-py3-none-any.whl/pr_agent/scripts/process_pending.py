#!/usr/bin/env python
# scripts/process_pending.py

import json
from datetime import datetime
import pandas as pd
from pathlib import Path

from pr_agent.core.metadata_manager import DirectoryMetadataStore
#from pr_agent.core.metadata_manager import load_metadata, mark_row
from pr_agent.core.text_extractor import extract_text
from pr_agent.core.summarizer import extract_summary
#from pr_agent.core.embedder import generate_embedding, save_embedding
from pr_agent.core.embedder import generate_embedding
from pr_agent.core.pinecone_manager import upsert_embedding
from pr_agent.core.json_writer import build_json_payload, write_json_file
# from pr_agent.settings import METADATA_DIR, EMBEDDINGS_DIR, RAW_DIR
# from pr_agent.settings import GDRIVE_FOLDER_ID

from pr_agent.settings import settings



def process_pending():
    # # 1) Load sheet
    # df = load_metadata()

    # 1) Open JSON store
    store = DirectoryMetadataStore(settings.METADATA_DIR)

    # for idx, row in df.iterrows():
    #     if row.get("Status", "") != "Pending":
    #         continue

    for doc_id in store.get_all_ids():
        meta = store.read(doc_id)
        if meta.get("Status") != "Pending":
            continue

        # doc_id   = row["Document ID"]
        # fname    = row["Original Filename"]
        # source   = row["Source System"]
        # drive_id = row.get("Drive File ID", "")

        fname  = meta["Original Filename"]
        source = meta["Source System"]


        print(f"Processing {fname} (Doc ID: {doc_id}, Source: {source})…")

        # 2) Based on source, we need to fetch raw_bytes again. 
        #    But since discover already pulled bytes into memory, 
        #    we actually stored NOTHING in the sheet except IDs.
        #    → So we need to re-invoke the correct connector to get bytes:
        from pr_agent.connectors.gdrive_connector import list_new_items as list_gdrive
        #from pr_agent.connectors.notion_connector import list_new_items as list_notion

        existing = set()  # we just want to fetch this single item
        if source == "GoogleDrive":
            items = list_gdrive(existing, settings.GDRIVE_FOLDER_ID)
            #print("DEBUG: Drive connector returned these names:", [it.name for it in items])
            matches = [it for it in items if it.name == fname]

        else:  # source == "Notion"
            matches = [it for it in list_notion(existing) if it.name == fname]

        if not matches:
            # Update the JSON metadata instead of Excel:
            meta = store.read(doc_id)
            meta["Status"] = "Error: Cannot fetch bytes"
            store.upsert(doc_id, meta)
            print(f"⚠ Unable to re-fetch {fname} from {source}. Skipping.")
            continue

        item = matches[0]

        # 3) Extract raw text in memory
        raw_text = extract_text(item)

        # 3.b) Write raw text out as JSON in RAW_DIR
        raw_path = Path(settings.RAW_DIR)
        raw_path.mkdir(parents=True, exist_ok=True)
        raw_json = raw_path / f"{doc_id}_raw.json"
        with open(raw_json, "w", encoding="utf-8") as rf:
            json.dump(
                {"document_id": doc_id, "raw_text": raw_text},
                rf,
                ensure_ascii=False,
                indent=2
            )
        print(f"Wrote raw text JSON to {raw_json}")

        if not raw_text:
            #mark_row(df, idx, {"Status": "Needs OCR"})
            meta["Status"] = "Needs OCR"
            store.upsert(doc_id, meta)

            continue

        # 4) Summarize (using summarizer.py)
        summary = extract_summary(raw_text)

        # 5) Generate embedding over the summary (not raw text)
        vector   = generate_embedding(summary)
        #emb_path = save_embedding(vector, doc_id, str(settings.EMBEDDINGS_DIR))
        ingest_ts = datetime.utcnow().isoformat() + "Z"
        emb_path = f"PineconeIndex<{settings.PINECONE_INDEX}>/{doc_id}"
        # Push into Pinecone
        # upsert_embedding(
        #     doc_id=doc_id,
        #     vector=vector,
        #     metadata={
        #     "source": source,
        #     "original_filename": fname,
        #     #"ingested_at": ingest_ts
        #     }
        # )
        #emb_path = f"PineconeIndex<{settings.PINECONE_INDEX}>/{doc_id}"

        # # 6) Flip status → “Processed” and set “Ingested At”
        # ingest_ts = datetime.utcnow().strftime("%Y-%m-%dT%H:%M:%SZ")
        # mark_row(df, idx, {"Status": "Processed", "Ingested At": ingest_ts})

        # 6) Flip status → “Processed” and set “Ingested At”
        #ingest_ts = datetime.utcnow().isoformat() + "Z"
        meta.update({
            "Status":            "Processed",
            "Ingested At":       ingest_ts,
            "Summary":           summary,
            "Embedding File Path / ID": emb_path
        })
        store.upsert(doc_id, meta)

        upsert_embedding(
            doc_id=doc_id,
            vector=vector,
            metadata=meta
        )

        # 10) Build JSON payload
        #     Coerce any NaN → "" first
        # def safe(val):
        #     return "" if pd.isna(val) else str(val)

        # metadata_row = {col: safe(row[col]) for col in df.columns}

        payload = build_json_payload(meta, summary, emb_path)

        # payload = build_json_payload(
        #     metadata_row,
        #     summary=summary,
        #     embedding_path=emb_path
        # )

        # 11) Write JSON to disk
        write_json_file(payload, doc_id, str(settings.METADATA_DIR))


        # 12) Update sheet with NLP fields
        # updates = {
        #     "Summary":                 summary,
        #     "Embedding File Path / ID":emb_path
        # }
        # mark_row(df, idx, updates)
        # print(f"Processed {fname}. JSON & sheet updated.")

        print(f"Processed {fname}. Metadata JSON updated.")


    print("All pending items have been processed.")

def main():
    process_pending()

if __name__ == "__main__":
    main()
