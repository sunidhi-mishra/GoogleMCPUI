from __future__ import annotations

import sys
from pathlib import Path
import unittest

SRC_PATH = Path(__file__).resolve().parents[1] / "src"
if str(SRC_PATH) not in sys.path:
    sys.path.insert(0, str(SRC_PATH))

from google_mcp_server.core import (
    document_append_index,
    extract_document_text,
    extract_message_text,
    search_text,
    summarize_gmail_message,
)


class CoreHelpersTests(unittest.TestCase):
    def test_extract_message_text_prefers_plain_text(self) -> None:
        message = {
            "snippet": "fallback",
            "payload": {
                "headers": [
                    {"name": "Subject", "value": "Hello"},
                ],
                "mimeType": "multipart/alternative",
                "parts": [
                    {
                        "mimeType": "text/plain",
                        "body": {"data": "SGVsbG8gd29ybGQh"},
                    }
                ],
            },
        }

        self.assertEqual(extract_message_text(message), "Hello world!")

    def test_summarize_gmail_message_collects_headers(self) -> None:
        message = {
            "id": "msg-1",
            "threadId": "thread-1",
            "snippet": "short",
            "payload": {
                "headers": [
                    {"name": "From", "value": "Alice <alice@example.com>"},
                    {"name": "Subject", "value": "Meeting"},
                ],
                "mimeType": "text/plain",
                "body": {"data": "VGV4dA"},
            },
        }

        summary = summarize_gmail_message(message)
        self.assertEqual(summary["from"], "Alice <alice@example.com>")
        self.assertEqual(summary["subject"], "Meeting")
        self.assertEqual(summary["id"], "msg-1")

    def test_extract_document_text_flattens_paragraphs(self) -> None:
        document = {
            "body": {
                "content": [
                    {
                        "paragraph": {
                            "elements": [
                                {"textRun": {"content": "Hello "}},
                                {"textRun": {"content": "Docs"}},
                            ]
                        }
                    }
                ]
            }
        }

        self.assertEqual(extract_document_text(document), "Hello Docs")

    def test_search_text_returns_context(self) -> None:
        matches = search_text("Alpha beta gamma beta delta", "beta", max_matches=2, context=5)

        self.assertEqual(len(matches), 2)
        self.assertEqual(matches[0]["start"], 6)
        self.assertIn("beta", matches[0]["excerpt"])

    def test_document_append_index_uses_last_end_index(self) -> None:
        document = {"body": {"content": [{"endIndex": 7}]}}
        self.assertEqual(document_append_index(document), 6)


if __name__ == "__main__":
    unittest.main()
