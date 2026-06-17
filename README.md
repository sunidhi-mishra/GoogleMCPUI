# Google MCP Web Dashboard

A Python MCP server for Google Workspace that exposes Gmail and Google Docs actions through a web dashboard. Build web applications, dashboards, and integrations that work with your Google account.

## Features

- **Gmail**: Search messages, retrieve threads, read messages
- **Google Docs**: Fetch documents, search text, create and edit documents
- **Web Dashboard**: Browser-based UI for testing and managing MCP tools
- **OAuth Web Flow**: Server-side OAuth authentication for multi-user deployments

## Quick Start

### 1. Set up Google OAuth (Web Application)

See [GOOGLE_SETUP.md](/e:/SideProjects/MCPv2.0/GOOGLE_SETUP.md) for detailed steps. In short:

- Create a Google Cloud project
- Enable Gmail API and Google Docs API
- Create OAuth 2.0 credentials for a **Web application** (not desktop)
- Set environment variables with your credentials

### 2. Start the Dashboard

```bash
streamlit run ui/streamlit_app.py
```

Then open `http://localhost:8501` in your browser and click "Sign in with Google"

### 3. Use the Tools

Once authenticated, you can:
- Browse available MCP tools
- View their input schemas
- Call tools with custom arguments
- See results in real-time

## VS Code MCP config

This repo includes a `.vscode/mcp.json` entry that launches the server in stdio mode.

## Security notes

- Keep the OAuth client secrets file out of source control.
- The Gmail scope is read-only by default.
- Docs write actions require the Google Docs write scope.
"# GoogleMCPUI" 
