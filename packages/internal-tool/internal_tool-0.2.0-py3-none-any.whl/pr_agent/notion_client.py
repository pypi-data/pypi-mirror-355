# pr_agent/notion_client.py

import requests
import time
from typing import Optional

from pr_agent.settings import settings



def _get_notion_headers() -> dict:
    """
    Returns the HTTP headers required for every Notion API call.
    Includes Authorization and Notion-Version.
    """
    return {
        "Authorization": f"Bearer {settings.NOTION_TOKEN}",
        "Notion-Version": "2022-06-28",
        "Content-Type": "application/json"
    }


def get_page(page_id: str) -> dict:
    """
    GET /v1/pages/{page_id}
    Returns: JSON describing the page’s properties.
    """
    url = f"https://api.notion.com/v1/pages/{page_id}"
    headers = _get_notion_headers()

    resp = requests.get(url, headers=headers)
    resp.raise_for_status()
    return resp.json()


def list_block_children(block_id: str, start_cursor: Optional[str] = None) -> dict:
    """
    GET /v1/blocks/{block_id}/children[?start_cursor=…]
    Returns one “page” of child-blocks under block_id.
      - results: List of block objects
      - has_more: bool
      - next_cursor: Optional[str]
    """
    url = f"https://api.notion.com/v1/blocks/{block_id}/children"
    headers = _get_notion_headers()
    params = {}
    if start_cursor:
        params["start_cursor"] = start_cursor

    resp = requests.get(url, headers=headers, params=params)
    resp.raise_for_status()
    return resp.json()


def query_database(database_id: str, start_cursor: Optional[str] = None) -> dict:
    """
    POST /v1/databases/{database_id}/query
    Returns one “page” of results from that database (each row is a page object).
      - results: List of page objects
      - has_more: bool
      - next_cursor: Optional[str]
    """
    url = f"https://api.notion.com/v1/databases/{database_id}/query"
    headers = _get_notion_headers()
    body = {}
    if start_cursor:
        body["start_cursor"] = start_cursor

    resp = requests.post(url, headers=headers, json=body)
    resp.raise_for_status()
    return resp.json()


def download_file(file_url: str, max_retries: int = 3, backoff: float = 1.0) -> bytes:
    """
    Download raw bytes from a Notion-hosted file/image URL.
    Retries on 429/5xx errors with exponential backoff.
    Returns: raw bytes
    """
    for attempt in range(1, max_retries + 1):
        resp = requests.get(file_url)
        if resp.status_code == 200:
            return resp.content

        if resp.status_code in (429, 500, 502, 503, 504) and attempt < max_retries:
            time.sleep(backoff * attempt)
            continue

        resp.raise_for_status()

    # If it still fails after retries, raise
    resp.raise_for_status()


def extract_page_title(page_json: dict) -> str:
    """
    Given the JSON from get_page(), pull out the “Name” property (type=title).
    Returns a short string or empty if no title found.
    """
    props = page_json.get("properties", {})
    name_prop = props.get("Name", {}).get("title", [])
    if isinstance(name_prop, list) and len(name_prop) > 0:
        return name_prop[0].get("plain_text", "")
    return ""


def fetch_all_block_children(block_id: str) -> list[dict]:
    """
    Pagination helper around list_block_children().
    Returns a flat list of every block under block_id.
    """
    all_results = []
    cursor = None

    while True:
        resp = list_block_children(block_id, start_cursor=cursor)
        all_results.extend(resp.get("results", []))
        if not resp.get("has_more"):
            break
        cursor = resp.get("next_cursor")

    return all_results


def fetch_all_database_rows(database_id: str) -> list[dict]:
    """
    Pagination helper around query_database().
    Returns a flat list of every row (each row is a page object) in the database.
    """
    all_rows = []
    cursor = None

    while True:
        resp = query_database(database_id, start_cursor=cursor)
        all_rows.extend(resp.get("results", []))
        if not resp.get("has_more"):
            break
        cursor = resp.get("next_cursor")

    return all_rows
