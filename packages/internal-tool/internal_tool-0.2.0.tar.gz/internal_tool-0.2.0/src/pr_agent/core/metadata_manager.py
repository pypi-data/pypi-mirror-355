# pr_agent/core/metadata_manager.py

import json
from pathlib import Path

def next_document_id(existing_ids: set[str]) -> str:
    """DIVAMI_001, DIVAMI_002… based on numeric suffixes in existing_ids."""
    suffixes = [
        int(d.split("_")[-1])
        for d in existing_ids
        if d.startswith("DIVAMI_") and d.split("_")[-1].isdigit()
    ]
    n = max(suffixes) + 1 if suffixes else 1
    return f"DIVAMI_{n:03d}"

class DirectoryMetadataStore:
    """
    Stores one JSON file per document under metadata_dir.
    Filename = {doc_id}.json
    """
    def __init__(self, metadata_dir: str):
        self.dir = Path(metadata_dir)
        self.dir.mkdir(parents=True, exist_ok=True)

    def get_all_ids(self) -> set[str]:
        return {p.stem for p in self.dir.glob("*.json")}

    def read(self, doc_id: str) -> dict | None:
        path = self.dir / f"{doc_id}.json"
        return json.loads(path.read_text(encoding="utf-8")) if path.exists() else None

    def upsert(self, doc_id: str, metadata: dict):
        path = self.dir / f"{doc_id}.json"
        tmp  = path.with_suffix(".json.tmp")
        tmp.write_text(json.dumps(metadata, indent=2, ensure_ascii=False),
                       encoding="utf-8")
        tmp.replace(path)
