"""Pure helpers for Gmail and Google Docs payload processing."""

from __future__ import annotations

from base64 import urlsafe_b64decode
from typing import Any


def _decode_base64url(value: str) -> str:
    padding = "=" * (-len(value) % 4)
    decoded = urlsafe_b64decode(value + padding)
    return decoded.decode("utf-8", errors="replace")


def extract_message_headers(message: dict[str, Any]) -> dict[str, str]:
    payload = message.get("payload", {})
    headers: dict[str, str] = {}
    for header in payload.get("headers", []):
        name = str(header.get("name", "")).strip().lower()
        if name:
            headers[name] = str(header.get("value", ""))
    return headers


def _extract_message_text_from_part(part: dict[str, Any]) -> str:
    mime_type = str(part.get("mimeType", ""))
    body = part.get("body", {})
    data = body.get("data")

    child_parts = part.get("parts", [])
    text_fragments: list[str] = []
    for child in child_parts:
        child_text = _extract_message_text_from_part(child)
        if child_text:
            text_fragments.append(child_text)

    if mime_type.startswith("text/") and data:
        decoded = _decode_base64url(str(data))
        if decoded.strip():
            return decoded

    if text_fragments:
        return "\n".join(text_fragments)

    if data:
        return _decode_base64url(str(data))

    return ""


def extract_message_text(message: dict[str, Any]) -> str:
    payload = message.get("payload", {})
    text = _extract_message_text_from_part(payload)
    if text.strip():
        return text.strip()
    snippet = str(message.get("snippet", "")).strip()
    return snippet


def summarize_gmail_message(message: dict[str, Any]) -> dict[str, Any]:
    headers = extract_message_headers(message)
    return {
        "id": message.get("id"),
        "threadId": message.get("threadId"),
        "labelIds": message.get("labelIds", []),
        "snippet": message.get("snippet", ""),
        "historyId": message.get("historyId"),
        "internalDate": message.get("internalDate"),
        "from": headers.get("from", ""),
        "to": headers.get("to", ""),
        "subject": headers.get("subject", ""),
        "date": headers.get("date", ""),
        "text": extract_message_text(message),
    }


def _extract_document_block_text(block: dict[str, Any]) -> list[str]:
    fragments: list[str] = []

    paragraph = block.get("paragraph")
    if paragraph:
        for element in paragraph.get("elements", []):
            text_run = element.get("textRun")
            if text_run and text_run.get("content"):
                fragments.append(str(text_run["content"]))
        return fragments

    table = block.get("table")
    if table:
        for row in table.get("tableRows", []):
            for cell in row.get("tableCells", []):
                for cell_block in cell.get("content", []):
                    fragments.extend(_extract_document_block_text(cell_block))
        return fragments

    for nested in block.get("content", []):
        fragments.extend(_extract_document_block_text(nested))

    return fragments


def extract_document_text(document: dict[str, Any]) -> str:
    body = document.get("body", {})
    fragments: list[str] = []
    for block in body.get("content", []):
        fragments.extend(_extract_document_block_text(block))

    text = "".join(fragments)
    return text.strip()


def search_text(text: str, query: str, max_matches: int = 10, context: int = 80) -> list[dict[str, Any]]:
    if not query.strip():
        return []

    haystack = text.casefold()
    needle = query.casefold()
    matches: list[dict[str, Any]] = []
    start = 0

    while len(matches) < max_matches:
        index = haystack.find(needle, start)
        if index < 0:
            break

        match_end = index + len(query)
        excerpt_start = max(0, index - context)
        excerpt_end = min(len(text), match_end + context)
        matches.append(
            {
                "start": index,
                "end": match_end,
                "excerpt": text[excerpt_start:excerpt_end],
            }
        )
        start = max(match_end, index + 1)

    return matches


def document_append_index(document: dict[str, Any]) -> int:
    body = document.get("body", {})
    content = body.get("content", [])
    if not content:
        return 1

    last_block = content[-1]
    end_index = int(last_block.get("endIndex", 1) or 1)
    return max(1, end_index - 1)
