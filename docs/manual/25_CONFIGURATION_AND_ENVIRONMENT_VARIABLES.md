# Chapter 25: Configuration & Environment Variables

## Environment File: `.env`

| Variable | Description | Required | Default |
| :--- | :--- | :--- | :--- |
| `GEMINI_API_KEY` | Google Gemini API Key for Cognitive Planning & Reasoning | Yes | - |
| `GROQ_API_KEY` | Groq API Key for Whisper Large Turbo STT | Yes | - |
| `NOVA_ENCRYPTION_KEY` | 32-byte Base64 key for AES-GCM credential encryption | No | Auto-generated dev key |
| `BACKEND_PORT` | Port for FastAPI HTTP/WebSocket server | No | `8000` |
| `LOG_LEVEL` | Application logging verbosity (`DEBUG`, `INFO`, `WARNING`) | No | `INFO` |
| `AUTO_ADB_ENABLED` | Enable background discovery of Wireless Android devices | No | `true` |
| `CHROMA_PERSIST_DIR` | Filesystem path for vector database storage | No | `./chroma_db` |
