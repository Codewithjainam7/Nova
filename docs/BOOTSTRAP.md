# NOVA Runtime Bootstrap

## 1. Startup Sequence
When `backend/main.py` executes, it starts a Uvicorn ASGI server and triggers the FastAPI `lifespan` context manager.
1. **SettingsSystem**: Loads `.env` and `.env.local`, mounts the configuration DI container.
2. **NovaKernel**: Executes the startup sequence, verifying the internal State Manager and Event Bus.
3. **ChatSystem**: Is injected during startup for UI presentation.
4. **WebSocket Listeners**: Open for business, awaiting UI connections.

## 2. Endpoints
### REST API (Port 8000)
- `GET /health` - Liveness probe (returns HTTP 200).
- `GET /ready` - Readiness probe (returns Kernel state).
- `GET /version` - Outputs semver and build environment.
- `GET /metrics` - Dumps telemetry for Kernel, Settings, and Chat subsystems.
- `POST /chat` - Sync REST fallback for Chat UI.

### WebSockets (Port 8000)
- `ws://localhost:8000/ws/chat` - Full duplex streaming chat. Sends and receives JSON payloads.
- `ws://localhost:8000/ws/events` - Pub/Sub event bridge for the Dynamic Island.

## 3. Environment Variables
Loaded via `python-dotenv`:
- `NOVA_ENV`: (e.g. `development`, `production`)
- `NOVA_DEBUG`: `true` or `false`
- `LOG_LEVEL`: Native logging level (`INFO`, `DEBUG`).

## 4. WebSocket Protocol (Chat)
**Client Request:**
```json
{
  "content": "Hello NOVA",
  "conversation_id": "default"
}
```

**Server Response:**
```json
{
  "type": "message",
  "message": {
    "id": "uuid-1234",
    "role": "assistant",
    "content": "Simulated Response: Hello NOVA"
  }
}
```
