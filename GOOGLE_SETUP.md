# Google OAuth Setup Guide (Web Dashboard)

Follow these steps to connect the MCP dashboard to your Google account.

## Step 1: Create a Google Cloud Project

1. Go to [Google Cloud Console](https://console.cloud.google.com/)
2. Click the project dropdown at the top and select "New Project"
3. Enter a project name (e.g., "Google MCP Dashboard") and click Create
4. Wait for the project to be created, then select it

## Step 2: Enable Required APIs

1. In the Cloud Console, search for "Gmail API"
2. Click on it and press "Enable"
3. Search for "Google Docs API"
4. Click on it and press "Enable"

## Step 3: Create OAuth 2.0 Credentials for Web

1. In the Cloud Console, go to **Credentials** (left sidebar)
2. Click **+ Create Credentials** → **OAuth client ID**
3. If prompted, click **Configure OAuth consent screen first**
   - Choose **External** user type
   - Fill in the required fields (app name, email, etc.)
   - Under **Scopes**, add:
     - `https://www.googleapis.com/auth/gmail.readonly`
     - `https://www.googleapis.com/auth/documents`
   - Save and continue
4. Back on the Credentials page, click **+ Create Credentials** → **OAuth client ID** again
5. Choose **Web application** as the application type
6. Under **Authorized redirect URIs**, add:
   - `http://localhost:8501/callback` (for local Streamlit)
   - `http://localhost:8000/callback` (for production)
7. Click Create
8. Click the **Download** button (or the download icon next to your credentials)

## Step 4: Set Environment Variables

Set these environment variables before running the dashboard:

```bash
# Windows (PowerShell)
$env:GOOGLE_MCP_CLIENT_ID = "your-client-id.apps.googleusercontent.com"
$env:GOOGLE_MCP_CLIENT_SECRET = "your-client-secret"
$env:GOOGLE_MCP_REDIRECT_URI = "http://localhost:8501/callback"
$env:GOOGLE_MCP_TOKEN_FILE = ".secrets/google_mcp_token.json"

# Or set in .env file and load with python-dotenv
```

Or create a `.env` file in the project root:

```env
GOOGLE_MCP_CLIENT_ID=your-client-id.apps.googleusercontent.com
GOOGLE_MCP_CLIENT_SECRET=your-client-secret
GOOGLE_MCP_REDIRECT_URI=http://localhost:8501/callback
GOOGLE_MCP_TOKEN_FILE=.secrets/google_mcp_token.json
```

## Step 5: First Run Authentication

1. Start the dashboard:
   ```bash
   streamlit run ui/streamlit_app.py
   ```

2. On first load, you'll see a "Login with Google" button

3. Click it, approve the permissions in Google's login screen, and you'll be redirected back

4. The token is saved locally and used for all future requests

## Testing the Connection

After logging in, you can test via the dashboard or use the test script:

```bash
python tools/test_integration.py
```

## Troubleshooting

- **"Client ID not set"**: Make sure environment variables or `.env` file is configured
- **"Invalid redirect URI"**: Ensure the redirect URI in `.env` matches what you set in Google Cloud Console
- **"Permission denied"**: Check that you granted the required scopes in Step 3
- **Token expired**: Delete `.secrets/google_mcp_token.json` and log in again
