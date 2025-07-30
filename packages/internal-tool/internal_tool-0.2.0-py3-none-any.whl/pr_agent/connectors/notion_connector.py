# pr_agent/connectors/notion_connector.py

import io
from typing import List, Tuple

from pr_agent.notion_client import (
    get_page,
    list_block_children,
    query_database,
    download_file,
    extract_page_title,
    fetch_all_block_children,
)
from pr_agent.connectors.base_connector import SourceItem
#from pr_agent.settings import NOTION_ROOT_PAGE_ID
from pr_agent.settings import settings

notion_root = settings.NOTION_ROOT_PAGE_ID

def process_leaf_page(page_id: str) -> List[SourceItem]:
    """
    Fetch all text blocks and attachments from a single Notion page (a “leaf”).
    Returns a list of SourceItem objects—one per attachment, or a single .txt if no attachments.
    """
    items: List[SourceItem] = []

    # 1) Fetch page metadata (to get title and last_edited_time)
    page_json = get_page(page_id)
    page_title = extract_page_title(page_json) or f"page_{page_id}"
    last_edited = page_json.get("last_edited_time", "")

    # 2) Fetch ALL child blocks of this page
    #    Use fetch_all_block_children for convenience (handles pagination)
    all_blocks = fetch_all_block_children(page_id)

    text_chunks: List[str] = []
    attachments: List[Tuple[str, io.BytesIO]] = []

    for block in all_blocks:
        btype = block["type"]

        # Textual content
        if btype in (
            "paragraph",
            "heading_1",
            "heading_2",
            "heading_3",
            "bulleted_list_item",
            "numbered_list_item",
        ):
            rich_array = block[btype].get("rich_text", [])
            content = "".join(rt.get("plain_text", "") for rt in rich_array)
            if content:
                text_chunks.append(content)

        # Image attachment
        elif btype == "image":
            file_obj = block["image"]["file"]
            url = file_obj.get("url")
            if url:
                raw_bytes = download_file(url)
                buf = io.BytesIO(raw_bytes)
                filename = url.split("/")[-1].split("?")[0]
                attachments.append((filename, buf, url))

        # File attachment (PDF, etc.)
        elif btype == "file":
            file_obj = block["file"]["file"]
            url = file_obj.get("url")
            if url:
                raw_bytes = download_file(url)
                buf = io.BytesIO(raw_bytes)
                # Notion sometimes supplies a “name” field under file_obj
                filename = file_obj.get("name", f"file_{block['id']}")
                attachments.append((filename, buf, url))

        else:
            # Skip child_page or child_database here because this function
            # is only called on true leaf pages (no further recursion).
            continue

    # 3) Turn each attachment into a SourceItem
    for filename, buffer in attachments:
        item_id = f"{page_id}:{filename}"
        items.append(
            SourceItem(
                id=item_id,
                name=filename,
                raw_bytes=buffer,
                last_modified=last_edited,
                source_system="Notion",
                url=file_url
            )
        )

    # 4) If no attachments but we have text, bundle text into a .txt SourceItem
    if not attachments and text_chunks:
        full_text = "\n\n".join(text_chunks)
        buffer = io.BytesIO(full_text.encode("utf-8"))
        txt_filename = f"{page_title.replace(' ', '_')}.txt"
        item_id = f"{page_id}:{txt_filename}"
        page_url = page_json.get("url") or f"https://www.notion.so/{page_id}"
        items.append(
            SourceItem(
                id=item_id,
                name=txt_filename,
                raw_bytes=buffer,
                last_modified=last_edited,
                source_system="Notion",
                url=page_url
            )
        )

    return items


def _walk_database_pages(response_json: dict) -> List[SourceItem]:
    """
    Given one “page” of results from query_database (each result is a page object),
    call process_leaf_page() on each and return a combined list.
    """
    items: List[SourceItem] = []
    for page in response_json.get("results", []):
        page_id = page["id"]
        items.extend(process_leaf_page(page_id))
    return items


def _walk_children_page(response_json: dict) -> List[SourceItem]:
    """
    Given one page of /blocks/{…}/children, inspect each block:
      - If it's a child_page → recurse via recursively_walk_block_tree
      - If it's a child_database → query that database and process its pages
      - Otherwise → skip (text/attachments on a leaf are handled in process_leaf_page)
    """
    items: List[SourceItem] = []

    for block in response_json.get("results", []):
        btype = block["type"]

        # 1) If it's a nested page, recurse into its subtree
        if btype == "child_page":
            child_page_id = block["id"]
            items.extend(recursively_walk_block_tree(child_page_id))

        # 2) If it's an inline database, query all rows and process each
        elif btype == "child_database":
            database_id = block["id"]
            # First “page” of results
            resp_db = query_database(database_id)
            items.extend(_walk_database_pages(resp_db))

            # Handle pagination for that database
            while resp_db.get("has_more"):
                cursor = resp_db.get("next_cursor")
                resp_db = query_database(database_id, start_cursor=cursor)
                items.extend(_walk_database_pages(resp_db))

        # 3) Otherwise: ignore (text and attachments in process_leaf_page)
        else:
            continue

    return items


# def recursively_walk_block_tree(root_id: str) -> List[SourceItem]:
#     """
#     Starting from a known root page ID (e.g. “Divami Documents”),
#     walk all child blocks under it. Whenever we see:
#       - child_page → recurse
#       - child_database → query and process each row as leaf
#       - plain blocks → skip (handled by process_leaf_page at leaf level)

#     Returns a flat list of all SourceItem found under that subtree.
#     """
#     all_items: List[SourceItem] = []

#     # 1) Fetch the first “page” of child blocks for root_id
#     resp = list_block_children(root_id)
#     all_items.extend(_walk_children_page(resp))

#     # 2) Handle pagination for root’s children
#     while resp.get("has_more"):
#         cursor = resp.get("next_cursor")
#         resp = list_block_children(root_id, start_cursor=cursor)
#         all_items.extend(_walk_children_page(resp))

#     return all_items

def recursively_walk_block_tree(page_id: str) -> List[SourceItem]:
    """
    Walk a Notion page and all its sub-pages, extracting text/attachments.
    """
    items: List[SourceItem] = []

    # 1) Always process this page as a leaf first
    items.extend(process_leaf_page(page_id))

    # 2) Then recurse into child pages & databases
    resp = list_block_children(page_id)
    while True:
        for block in resp.get("results", []):
            btype = block["type"]

            if btype == "child_page":
                # Recurse into that sub-page
                child_id = block["id"]
                items.extend(recursively_walk_block_tree(child_id))

            elif btype == "child_database":
                # For inline databases, process each row as a leaf
                from pr_agent.notion_client import query_database
                from pr_agent.connectors.notion_connector import _walk_database_pages

                db_id = block["id"]
                db_page = query_database(db_id)
                items.extend(_walk_database_pages(db_page))
                while db_page.get("has_more"):
                    db_page = query_database(db_id, start_cursor=db_page["next_cursor"])
                    items.extend(_walk_database_pages(db_page))

            else:
                # plain text/attachments are already handled by process_leaf_page
                continue

        if not resp.get("has_more"):
            break
        resp = list_block_children(page_id, start_cursor=resp["next_cursor"])

    return items



def list_new_items(existing_titles: set[str]) -> List[SourceItem]:
    """
    Entry point for discover_sources.py. Walk the entire Notion subtree under
    NOTION_ROOT_PAGE_ID, collect all SourceItem (attachments/text). Then filter out
    any whose .name is already in existing_titles, returning only new items.
    """
    all_items: List[SourceItem] = recursively_walk_block_tree(notion_root)
    new_items = [item for item in all_items if item.name not in existing_titles]
    return new_items
