"""MCP tools for Gmail and Google Docs."""

from __future__ import annotations

from functools import lru_cache
from typing import Any

from mcp.server.fastmcp import FastMCP

from .services import GoogleWorkspaceClient

mcp = FastMCP("google-gmail-docs", json_response=True)


@lru_cache(maxsize=1)
def get_google_client() -> GoogleWorkspaceClient:
    return GoogleWorkspaceClient()


@mcp.tool()
def gmail_search(query: str, max_results: int = 10, page_token: str | None = None) -> dict[str, Any]:
    """Search Gmail messages using Gmail query syntax."""
    return get_google_client().search_gmail(query=query, max_results=max_results, page_token=page_token)


@mcp.tool()
def gmail_get_message(message_id: str) -> dict[str, Any]:
    """Fetch a single Gmail message by ID."""
    return get_google_client().get_gmail_message(message_id=message_id)


@mcp.tool()
def gmail_list_threads(query: str = "", max_results: int = 10, page_token: str | None = None) -> dict[str, Any]:
    """List Gmail threads matching a search query."""
    return get_google_client().list_gmail_threads(query=query, max_results=max_results, page_token=page_token)


@mcp.tool()
def docs_get_document(document_id: str) -> dict[str, Any]:
    """Fetch a Google Doc and return its text content."""
    return get_google_client().get_document(document_id=document_id)


@mcp.tool()
def docs_search_document(document_id: str, query: str, max_matches: int = 10) -> dict[str, Any]:
    """Search for text inside a Google Doc."""
    return get_google_client().search_document_text(document_id=document_id, query=query, max_matches=max_matches)


@mcp.tool()
def docs_create_document(title: str, body_text: str | None = None) -> dict[str, Any]:
    """Create a new Google Doc."""
    return get_google_client().create_document(title=title, body_text=body_text)


@mcp.tool()
def docs_append_text(document_id: str, text: str) -> dict[str, Any]:
    """Append text to the end of a Google Doc."""
    return get_google_client().append_text(document_id=document_id, text=text)


def main() -> None:
    """Run the MCP server over stdio."""
    mcp.run()
