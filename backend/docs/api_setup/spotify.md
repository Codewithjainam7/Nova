# Spotify API Setup Guide

This guide explains how to connect NOVA directly to your Spotify account using the official Spotify Web API, bypassing the need for desktop UI automation.

## Service Details
- **Service Name**: Spotify
- **Authentication Method**: OAuth 2.0 (Authorization Code Flow)
- **Free Tier Information**: Spotify allows searching and reading basic profile data on the free tier. **However, playback control (Play, Pause, Skip) requires a Spotify Premium account.**

## Required Scopes
NOVA requires the following OAuth scopes to control your music:
- `user-read-playback-state`
- `user-modify-playback-state`
- `user-read-currently-playing`

## Step-by-step Credentials Guide

1. Navigate to the [Spotify Developer Dashboard](https://developer.spotify.com/dashboard).
2. Log in with your Spotify account.
3. Click on **Create App**.
4. Fill in the App Name (e.g., "NOVA AI OS") and Description.
5. In the **Redirect URIs** field, enter exactly: `http://localhost:8000/auth/spotify/callback`
6. Check the terms of service box and click **Save**.
7. Once created, click on the **Settings** button in your app dashboard.
8. Copy the **Client ID** and the **Client Secret**.

## Configuration in NOVA

You must place these credentials in your `.env` file located in the `backend/` directory:

```env
SPOTIFY_CLIENT_ID=your_client_id_here
SPOTIFY_CLIENT_SECRET=your_client_secret_here
```

After updating the `.env` file, go to the **Integrations** page in the NOVA settings and click **Connect** next to Spotify to complete the OAuth login flow.
