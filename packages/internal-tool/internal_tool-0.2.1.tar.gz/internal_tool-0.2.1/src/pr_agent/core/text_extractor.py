# pr_agent/core/text_extractor.py

import os
import pandas as pd
import pypandoc
from pr_agent.drive_client import fetch_file_bytes  # used only if you want to re-fetch, but optional

def extract_text(source_item) -> str:
    """
    Given a SourceItem (with raw_bytes and name), 
    return a plain-text string for PDF, DOCX, TXT, XLSX.
    """
    from io import BytesIO
    buffer = source_item.raw_bytes
    filename = source_item.name
    ext = os.path.splitext(filename)[1].lower()

    if ext in [".txt", ".md"]:
        return buffer.read().decode("utf-8", errors="ignore")
    
    elif ext == ".doc":
        import pypandoc
        try:
            raw = buffer.read()
            return pypandoc.convert_text(raw, to="plain", format="doc")
        except Exception:
            return ""


    elif ext == ".docx":
        from docx import Document
        try:
            doc = Document(buffer)
            return "\n".join([p.text for p in doc.paragraphs])
        except:
            return ""

    elif ext == ".pdf":
        from PyPDF2 import PdfReader
        try:
            reader = PdfReader(buffer)
            pages = [page.extract_text() or "" for page in reader.pages]
            return "\n".join(pages)
        except:
            return ""

    elif ext in [".xlsx", ".xls"]:
        try:
            df = pd.read_excel(buffer, engine="openpyxl")
            text_rows = df.astype(str).apply(lambda row: " ".join(row), axis=1)
            return "\n".join(text_rows.tolist())
        except:
            return ""

    else:
        return ""
