# Supported Integration Authentication Methods

NOVA supports two main types of API integrations: **OAuth 2.0** and **API Keys**. The authentication method determines how NOVA connects to the service and what credentials you need to provide.

## OAuth 2.0 Integrations

OAuth 2.0 is used for services that require NOVA to act on your behalf securely, often involving a web-based login flow.

*   **Spotify**
    *   **Usage**: Controlling playback, fetching currently playing track, searching catalog.
    *   **Setup**: Requires creating an app in the Spotify Developer Dashboard. NOVA will redirect you to Spotify to log in and grant permissions.

*   **Google Workspace (Gmail, Calendar)**
    *   **Usage**: Reading emails, sending emails, checking calendar events, creating calendar events.
    *   **Setup**: Requires setting up OAuth credentials in the Google Cloud Console. NOVA will redirect you to Google to log in.

## API Key Integrations

API Keys are static string tokens used for services that provide raw data or require direct authentication without a user consent screen.

*   **GitHub**
    *   **Usage**: Reading repository data, pushing commits, checking issues.
    *   **Setup**: Requires generating a Personal Access Token (PAT) from your GitHub Developer Settings.

*   **Weather APIs (e.g., OpenWeatherMap)**
    *   **Usage**: Fetching current weather and forecasts.
    *   **Setup**: Requires signing up for the service and obtaining an API key.

*   **LLM Providers (e.g., OpenAI, Anthropic, Gemini)**
    *   **Usage**: Powering the core Planner and Conversational Engine.
    *   **Setup**: Requires obtaining an API key from the respective provider's dashboard.

## Managing Connections

You can manage all connections in the NOVA **Integrations** Settings page.

*   **Connecting**: Clicking "Connect" on an OAuth service will pop open a browser window. Clicking "Connect" on an API Key service will prompt you to enter the key.
*   **Security**: All tokens and keys are encrypted locally using symmetric AES encryption (via Fernet) before being saved to the local SQLite database.
*   **Testing**: Use the "Test Connection" button to verify that the credentials are valid and the API is reachable.
