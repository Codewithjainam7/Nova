# Chapter 24: REST API Reference

## API Base URL
`http://localhost:8000`

## Endpoints

### 1. `POST /api/chat`
Submit a text query for processing.
- **Request Body**: `{"message": "string", "session_id": "optional-uuid"}`
- **Response**: `{"response": "string", "plan": {...}}`

### 2. `POST /api/voice/transcribe`
Upload raw audio WebM buffer for Groq Whisper STT transcription.
- **Request Body**: Binary audio payload (`audio/webm` or `audio/wav`)
- **Response**: `{"transcript": "string"}`

### 3. `GET /api/devices`
List connected Android and local automation devices.
- **Response**: `[{"id": "...", "name": "...", "status": "connected"}]`

### 4. `GET /api/settings`
Retrieve active user configuration and preferences profile.
- **Response**: `{"profile": "default", "theme": "dark", "voice": "female"}`
