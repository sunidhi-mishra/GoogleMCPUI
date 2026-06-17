# Copilot Instructions

This workspace contains a Python MCP server for Google Gmail and Google Docs.

## Project conventions

- Keep MCP tool definitions in `src/google_mcp_server/server.py`.
- Keep Google API and OAuth logic isolated in `src/google_mcp_server/services.py`.
- Keep pure parsing and text helpers in `src/google_mcp_server/core.py` so they can be unit tested without external APIs.
- Prefer the `MCPServer` API from the MCP Python SDK.
- Use stdio as the default transport for VS Code MCP integration.

## Relevant SDK references

- MCP Python SDK quickstart and server usage: https://github.com/modelcontextprotocol/python-sdk
- Python SDK docs index: https://github.com/modelcontextprotocol/python-sdk/blob/main/docs/index.md
- stdio server transport: https://github.com/modelcontextprotocol/python-sdk/blob/main/src/mcp/server/stdio.py

## Editing guidance

- Update `README.md` and `.vscode/mcp.json` when tool names or startup commands change.
- Keep Google scopes explicit and minimal.
- Do not hardcode secrets or tokens in source files.
