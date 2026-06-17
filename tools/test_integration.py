#!/usr/bin/env python3
"""Integration test to verify Gmail and Google Docs connectivity."""

from __future__ import annotations

import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent.parent / "src"))

from google_mcp_server.services import GoogleWorkspaceClient


def test_gmail_connection() -> None:
    """Test Gmail API connection."""
    print("\n=== Testing Gmail Connection ===")
    client = GoogleWorkspaceClient()

    try:
        print("Searching for recent emails...")
        result = client.search_gmail(query="", max_results=1)
        print(f"✓ Gmail API works!")
        print(f"  Found {result['resultSizeEstimate']} total messages in your mailbox")
        if result["messages"]:
            msg = result["messages"][0]
            print(f"  Most recent: {msg.get('subject', '[no subject]')} from {msg.get('from', '[unknown]')}")
    except Exception as exc:
        print(f"✗ Gmail API failed: {exc}")
        raise


def test_docs_connection() -> None:
    """Test Google Docs API connection."""
    print("\n=== Testing Google Docs Connection ===")
    client = GoogleWorkspaceClient()

    try:
        print("Creating a test document...")
        result = client.create_document(
            title="MCP Test Document",
            body_text="This is a test document created by the Google MCP Server.\n",
        )
        doc_id = result["documentId"]
        print(f"✓ Google Docs API works!")
        print(f"  Created document: {result['title']}")
        print(f"  Document ID: {doc_id}")
        print(f"  URL: {result.get('url', 'N/A')}")

        print("\nAppending text to the document...")
        updated = client.append_text(doc_id, "This text was added by an MCP tool call.\n")
        print(f"✓ Document updated successfully")
        print(f"  Current length: {len(updated['text'])} characters")

        print("\nSearching for text in the document...")
        search_result = client.search_document_text(doc_id, "MCP")
        print(f"✓ Document search works!")
        print(f"  Found {search_result['matchCount']} match(es) for 'MCP'")

    except Exception as exc:
        print(f"✗ Google Docs API failed: {exc}")
        raise


def main() -> None:
    """Run all integration tests."""
    print("=" * 50)
    print("Google MCP Server - Integration Test")
    print("=" * 50)

    try:
        test_gmail_connection()
        test_docs_connection()
        print("\n" + "=" * 50)
        print("✓ All tests passed!")
        print("=" * 50)
    except Exception:
        print("\n" + "=" * 50)
        print("✗ Integration test failed")
        print("=" * 50)
        sys.exit(1)


if __name__ == "__main__":
    main()
