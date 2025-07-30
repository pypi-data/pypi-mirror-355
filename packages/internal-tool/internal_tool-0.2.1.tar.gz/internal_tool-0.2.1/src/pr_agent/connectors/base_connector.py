# pr_agent/connectors/base_connector.py  (you can also just define it in each connector)
from dataclasses import dataclass
from io import BytesIO
from typing import Optional

@dataclass
class SourceItem:
    id: str               # unique ID in that source (e.g. Drive fileId or Notion blockId)
    name: str             # “filename” or title (e.g. “report.pdf” or “Project Notes”)
    raw_bytes: BytesIO    # In-memory bytes of the file, ready for text_extractor
    last_modified: str    # ISO8601 timestamp (if available), else blank
    source_system: str    # literal "GoogleDrive" or "Notion"
    url: Optional[str] = None
    mime_type: Optional[str] = None
