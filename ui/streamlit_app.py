"""Web dashboard UI for testing the Google MCP server."""

from __future__ import annotations

import asyncio
import json
import os
import sys
from pathlib import Path
from typing import Any

import streamlit as st
from mcp import ClientSession, StdioServerParameters
from mcp.client.stdio import stdio_client

sys.path.insert(0, str(Path(__file__).parent.parent / "src"))

from google_mcp_server.services import GoogleWorkspaceClient

PROJECT_ROOT = Path(__file__).resolve().parents[1]
DEFAULT_SERVER_COMMAND = sys.executable
DEFAULT_SERVER_ARGS = ["-m", "google_mcp_server"]


def _load_json_argument(raw_text: str) -> dict[str, Any]:
    text = raw_text.strip()
    if not text:
        return {}
    parsed = json.loads(text)
    if not isinstance(parsed, dict):
        raise ValueError("Tool arguments must be a JSON object.")
    return parsed


async def _list_tools(server_command: str, server_args: list[str]) -> list[dict[str, Any]]:
    params = StdioServerParameters(command=server_command, args=server_args, cwd=str(PROJECT_ROOT))
    async with stdio_client(params) as (read_stream, write_stream):
        async with ClientSession(read_stream, write_stream) as session:
            await session.initialize()
            response = await session.list_tools()
            return [tool.model_dump(exclude_none=True) for tool in response.tools]


async def _call_tool(
    server_command: str,
    server_args: list[str],
    tool_name: str,
    arguments: dict[str, Any],
) -> dict[str, Any]:
    params = StdioServerParameters(command=server_command, args=server_args, cwd=str(PROJECT_ROOT))
    async with stdio_client(params) as (read_stream, write_stream):
        async with ClientSession(read_stream, write_stream) as session:
            await session.initialize()
            result = await session.call_tool(tool_name, arguments=arguments)
            return result.model_dump(exclude_none=True)


def _run_async(coro: Any) -> Any:
    return asyncio.run(coro)


def _check_google_auth() -> bool:
    """Check if user is authenticated with Google."""
    token_file = Path(os.environ.get("GOOGLE_MCP_TOKEN_FILE", ".secrets/google_mcp_token.json"))
    return token_file.exists()


def _show_login_page() -> None:
    """Show the Google OAuth login page."""
    st.set_page_config(page_title="Google MCP Dashboard - Login", page_icon="🔐", layout="centered")

    st.markdown(
        """
        <style>
        .login-container { max-width: 500px; margin: auto; padding-top: 5rem; }
        .login-card {
          padding: 3rem;
          border-radius: 1rem;
          background: linear-gradient(135deg, #102a43 0%, #1f4e79 55%, #2d6a4f 100%);
          color: white;
          text-align: center;
          box-shadow: 0 12px 30px rgba(16, 42, 67, 0.18);
          margin-bottom: 2rem;
        }
        </style>
        """,
        unsafe_allow_html=True,
    )

    st.markdown("<div class='login-container'>", unsafe_allow_html=True)
    st.markdown("<div class='login-card'>", unsafe_allow_html=True)
    st.title("🔐 Google MCP Dashboard")
    st.markdown("### Connect your Google account to get started")

    if st.button("Sign in with Google", type="primary", use_container_width=True, key="login_btn"):
        try:
            client = GoogleWorkspaceClient()
            auth_url, state = client.get_authorization_url()
            st.session_state["oauth_state"] = state
            st.markdown(f"[👉 Click here to authorize]({auth_url})", unsafe_allow_html=True)
            st.info("After logging in, you'll be redirected. Paste the authorization code below.")

            code = st.text_input("Authorization Code", type="password", label_visibility="collapsed", key="auth_code")
            if code:
                with st.spinner("Exchanging code for token..."):
                    try:
                        client.exchange_code_for_token(code)
                        st.success("✓ Successfully authenticated!")
                        st.rerun()
                    except Exception as exc:
                        st.error(f"Failed to authenticate: {exc}")
        except ValueError as exc:
            st.error(f"Configuration error: {exc}\n\nPlease check GOOGLE_MCP_CLIENT_ID and GOOGLE_MCP_CLIENT_SECRET environment variables.")
        except Exception as exc:
            st.error(f"Authentication error: {exc}")

    st.markdown("</div>", unsafe_allow_html=True)
    st.markdown("---")
    st.markdown("### Setup Instructions")
    st.markdown("""
    1. Set up a Google Cloud project (see GOOGLE_SETUP.md)
    2. Set environment variables for your OAuth credentials
    3. Return here and click the login button
    """)
    st.markdown("</div>", unsafe_allow_html=True)


def main() -> None:
    st.set_page_config(page_title="Google MCP Dashboard", page_icon="📧", layout="wide")

    # Check authentication
    if not _check_google_auth():
        _show_login_page()
        return

    st.markdown(
        """
        <style>
        .block-container { padding-top: 2rem; }
        .title-card {
          padding: 1.25rem 1.5rem;
          border-radius: 1rem;
          background: linear-gradient(135deg, #102a43 0%, #1f4e79 55%, #2d6a4f 100%);
          color: white;
          box-shadow: 0 12px 30px rgba(16, 42, 67, 0.18);
          margin-bottom: 1.25rem;
        }
        .muted-card {
          border: 1px solid rgba(15, 23, 42, 0.12);
          border-radius: 0.9rem;
          padding: 1rem;
          background: rgba(248, 250, 252, 0.85);
          margin-bottom: 1rem;
        }
        </style>
        """,
        unsafe_allow_html=True,
    )

    st.markdown(
        """
        <div class="title-card">
          <h1 style="margin: 0;">📧 Google MCP Dashboard</h1>
          <p style="margin: 0.35rem 0 0 0; opacity: 0.9;">Connected tools for Gmail and Google Docs. List MCP tools, inspect their schema, and invoke actions.</p>
        </div>
        """,
        unsafe_allow_html=True,
    )

    with st.sidebar:
        st.header("Server")
        server_command = st.text_input("Python executable", value=DEFAULT_SERVER_COMMAND)
        server_args_text = st.text_area("Arguments", value=" ".join(DEFAULT_SERVER_ARGS), height=90)
        load_tools = st.button("Load tools", type="primary", use_container_width=True)
        
        if st.button("🚪 Logout", use_container_width=True):
            token_file = Path(os.environ.get("GOOGLE_MCP_TOKEN_FILE", ".secrets/google_mcp_token.json"))
            if token_file.exists():
                token_file.unlink()
            st.rerun()

        st.caption("The UI starts the MCP server over stdio for each request.")

    server_args = [arg for arg in server_args_text.split() if arg]

    if load_tools or "tools" not in st.session_state:
        with st.spinner("Loading tools from the MCP server..."):
            try:
                st.session_state["tools"] = _run_async(_list_tools(server_command, server_args))
                st.session_state["load_error"] = None
            except Exception as exc:
                st.session_state["tools"] = []
                st.session_state["load_error"] = str(exc)

    if st.session_state.get("load_error"):
        st.error(st.session_state["load_error"])

    tools: list[dict[str, Any]] = st.session_state.get("tools", [])
    if not tools:
        st.info("Load the server tools to begin testing.")
        return

    tool_names = [tool.get("name", "") for tool in tools]
    selected_tool_name = st.selectbox("Tool", tool_names)
    selected_tool = next(tool for tool in tools if tool.get("name") == selected_tool_name)

    left, right = st.columns([1, 1])
    with left:
        st.markdown('<div class="muted-card">', unsafe_allow_html=True)
        st.subheader("Tool details")
        st.json(selected_tool)
        st.markdown("</div>", unsafe_allow_html=True)

    with right:
        st.markdown('<div class="muted-card">', unsafe_allow_html=True)
        st.subheader("Arguments")
        raw_arguments = st.text_area("JSON arguments", value="{}", height=220, label_visibility="collapsed")
        run_tool = st.button("Call tool", type="primary", use_container_width=True)
        st.markdown("</div>", unsafe_allow_html=True)

    if run_tool:
        try:
            arguments = _load_json_argument(raw_arguments)
            with st.spinner(f"Calling {selected_tool_name}..."):
                result = _run_async(_call_tool(server_command, server_args, selected_tool_name, arguments))
            st.success("Tool call completed.")
            st.subheader("Result")
            st.json(result)
        except Exception as exc:
            st.error(str(exc))


if __name__ == "__main__":
    main()