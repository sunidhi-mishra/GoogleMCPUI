"""Google API client wrappers and authentication helpers."""

from __future__ import annotations

import json
import os
from dataclasses import dataclass, field
from pathlib import Path
from typing import Any

from google.auth.transport.requests import Request
from google.oauth2.credentials import Credentials
from google_auth_oauthlib.flow import Flow
from googleapiclient.discovery import build

from .core import document_append_index, extract_document_text, search_text, summarize_gmail_message

DEFAULT_SCOPES = (
    "https://www.googleapis.com/auth/gmail.readonly",
    "https://www.googleapis.com/auth/documents",
)


def _parse_scopes(raw_scopes: str | None) -> tuple[str, ...]:
    if not raw_scopes:
        return DEFAULT_SCOPES
    scopes = [scope.strip() for scope in raw_scopes.split(",") if scope.strip()]
    return tuple(scopes) or DEFAULT_SCOPES


@dataclass(slots=True)
class GoogleMCPConfig:
    client_id: str = field(default_factory=lambda: os.environ.get("GOOGLE_MCP_CLIENT_ID", ""))
    client_secret: str = field(default_factory=lambda: os.environ.get("GOOGLE_MCP_CLIENT_SECRET", ""))
    redirect_uri: str = field(
        default_factory=lambda: os.environ.get("GOOGLE_MCP_REDIRECT_URI", "http://localhost:8501/callback")
    )
    token_file: Path = field(
        default_factory=lambda: Path(os.environ.get("GOOGLE_MCP_TOKEN_FILE", ".secrets/google_mcp_token.json")).expanduser()
    )
    scopes: tuple[str, ...] = field(default_factory=lambda: _parse_scopes(os.environ.get("GOOGLE_MCP_SCOPES")))
    gmail_user_id: str = field(default_factory=lambda: os.environ.get("GOOGLE_MCP_GMAIL_USER_ID", "me"))
    docs_user_id: str = field(default_factory=lambda: os.environ.get("GOOGLE_MCP_DOCS_USER_ID", "me"))


class GoogleWorkspaceClient:
    """Lazily authenticates and caches Google API service clients."""

    def __init__(self, config: GoogleMCPConfig | None = None) -> None:
        self.config = config or GoogleMCPConfig()
        self._credentials: Credentials | None = None
        self._gmail_service: Any | None = None
        self._docs_service: Any | None = None

    def _load_credentials(self) -> Credentials:
        if self._credentials is not None:
            return self._credentials

        credentials: Credentials | None = None
        if self.config.token_file.exists():
            try:
                credentials = Credentials.from_authorized_user_file(str(self.config.token_file), list(self.config.scopes))
            except Exception as exc:
                raise ValueError(f"Invalid token file: {exc}")

        if credentials and credentials.expired and credentials.refresh_token:
            credentials.refresh(Request())
        elif credentials is None:
            if not self.config.client_id or not self.config.client_secret:
                raise ValueError(
                    "Google OAuth not configured. Set GOOGLE_MCP_CLIENT_ID and GOOGLE_MCP_CLIENT_SECRET "
                    "environment variables and authenticate via the web dashboard."
                )

        if credentials is None:
            raise RuntimeError(
                "No credentials available. Please log in via the web dashboard first."
            )

        self.config.token_file.parent.mkdir(parents=True, exist_ok=True)
        self.config.token_file.write_text(credentials.to_json(), encoding="utf-8")
        self._credentials = credentials
        return credentials

    def get_authorization_url(self) -> tuple[str, str]:
        """Generate OAuth authorization URL for web flow.
        
        Returns:
            (authorization_url, state) - the URL to redirect user to, and the state token
        """
        if not self.config.client_id or not self.config.client_secret:
            raise ValueError("Client ID and secret must be configured")

        flow = Flow.from_client_config(
            {
                "installed": {
                    "client_id": self.config.client_id,
                    "client_secret": self.config.client_secret,
                    "auth_uri": "https://accounts.google.com/o/oauth2/auth",
                    "token_uri": "https://oauth2.googleapis.com/token",
                }
            },
            scopes=list(self.config.scopes),
            redirect_uri=self.config.redirect_uri,
        )
        authorization_url, state = flow.authorization_url(prompt="consent")
        return authorization_url, state

    def exchange_code_for_token(self, code: str) -> None:
        """Exchange authorization code for access token (after redirect from Google)."""
        if not self.config.client_id or not self.config.client_secret:
            raise ValueError("Client ID and secret must be configured")

        flow = Flow.from_client_config(
            {
                "installed": {
                    "client_id": self.config.client_id,
                    "client_secret": self.config.client_secret,
                    "auth_uri": "https://accounts.google.com/o/oauth2/auth",
                    "token_uri": "https://oauth2.googleapis.com/token",
                }
            },
            scopes=list(self.config.scopes),
            redirect_uri=self.config.redirect_uri,
        )
        flow.fetch_token(code=code)
        credentials = flow.credentials
        if credentials is None:
            raise RuntimeError("Failed to exchange code for credentials")

        self.config.token_file.parent.mkdir(parents=True, exist_ok=True)
        self.config.token_file.write_text(credentials.to_json(), encoding="utf-8")
        self._credentials = credentials

    def gmail(self) -> Any:
        if self._gmail_service is None:
            self._gmail_service = build("gmail", "v1", credentials=self._load_credentials(), cache_discovery=False)
        return self._gmail_service

    def docs(self) -> Any:
        if self._docs_service is None:
            self._docs_service = build("docs", "v1", credentials=self._load_credentials(), cache_discovery=False)
        return self._docs_service

    def search_gmail(
        self,
        query: str,
        max_results: int = 10,
        page_token: str | None = None,
        user_id: str | None = None,
    ) -> dict[str, Any]:
        service = self.gmail()
        response = (
            service.users()
            .messages()
            .list(
                userId=user_id or self.config.gmail_user_id,
                q=query,
                maxResults=max_results,
                pageToken=page_token,
            )
            .execute()
        )

        messages: list[dict[str, Any]] = []
        for entry in response.get("messages", []):
            message = (
                service.users()
                .messages()
                .get(userId=user_id or self.config.gmail_user_id, id=entry["id"], format="full")
                .execute()
            )
            messages.append(summarize_gmail_message(message))

        return {
            "query": query,
            "count": len(messages),
            "resultSizeEstimate": response.get("resultSizeEstimate", 0),
            "nextPageToken": response.get("nextPageToken"),
            "messages": messages,
        }

    def get_gmail_message(self, message_id: str, user_id: str | None = None) -> dict[str, Any]:
        service = self.gmail()
        message = (
            service.users()
            .messages()
            .get(userId=user_id or self.config.gmail_user_id, id=message_id, format="full")
            .execute()
        )
        return summarize_gmail_message(message)

    def list_gmail_threads(
        self,
        query: str = "",
        max_results: int = 10,
        page_token: str | None = None,
        user_id: str | None = None,
    ) -> dict[str, Any]:
        service = self.gmail()
        response = (
            service.users()
            .threads()
            .list(
                userId=user_id or self.config.gmail_user_id,
                q=query or None,
                maxResults=max_results,
                pageToken=page_token,
            )
            .execute()
        )
        return {
            "query": query,
            "count": len(response.get("threads", [])),
            "resultSizeEstimate": response.get("resultSizeEstimate", 0),
            "nextPageToken": response.get("nextPageToken"),
            "threads": response.get("threads", []),
        }

    def get_document(self, document_id: str) -> dict[str, Any]:
        service = self.docs()
        document = service.documents().get(documentId=document_id).execute()
        return {
            "documentId": document.get("documentId"),
            "title": document.get("title", ""),
            "text": extract_document_text(document),
            "raw": document,
        }

    def search_document_text(self, document_id: str, query: str, max_matches: int = 10) -> dict[str, Any]:
        service = self.docs()
        document = service.documents().get(documentId=document_id).execute()
        text = extract_document_text(document)
        return {
            "documentId": document.get("documentId"),
            "title": document.get("title", ""),
            "query": query,
            "matchCount": len(search_text(text, query, max_matches=max_matches)),
            "matches": search_text(text, query, max_matches=max_matches),
        }

    def create_document(self, title: str, body_text: str | None = None) -> dict[str, Any]:
        service = self.docs()
        document = service.documents().create(body={"title": title}).execute()
        document_id = document.get("documentId")

        if body_text and document_id:
            normalized_text = body_text if body_text.endswith("\n") else f"{body_text}\n"
            service.documents().batchUpdate(
                documentId=document_id,
                body={
                    "requests": [
                        {
                            "insertText": {
                                "location": {"index": 1},
                                "text": normalized_text,
                            }
                        }
                    ]
                },
            ).execute()

        return {
            "documentId": document_id,
            "title": document.get("title", title),
            "url": document.get("documentUrl"),
            "raw": document,
        }

    def append_text(self, document_id: str, text: str) -> dict[str, Any]:
        service = self.docs()
        document = service.documents().get(documentId=document_id).execute()
        insertion_index = document_append_index(document)
        normalized_text = text if text.endswith("\n") else f"{text}\n"
        service.documents().batchUpdate(
            documentId=document_id,
            body={
                "requests": [
                    {
                        "insertText": {
                            "location": {"index": insertion_index},
                            "text": normalized_text,
                        }
                    }
                ]
            },
        ).execute()

        updated_document = service.documents().get(documentId=document_id).execute()
        return {
            "documentId": document_id,
            "title": updated_document.get("title", ""),
            "text": extract_document_text(updated_document),
            "raw": updated_document,
        }
