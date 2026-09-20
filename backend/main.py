import asyncio
import time
import json
from contextlib import asynccontextmanager
from fastapi import FastAPI, WebSocket, WebSocketDisconnect
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel

from backend.settings.core import SettingsSystem
from backend.kernel.core import NovaKernel, KernelLogger
from backend.kernel.schema import KernelRequest, KernelState
from backend.kernel.events import KernelEventBus
from backend.chat.core import ChatSystem
from backend.chat.schema import ChatMessage, ChatMessageType
from backend.core.logger import app_logger
import os
from backend.core.environment import load_environment
load_environment()

from backend.providers.core import AIProviderManager
from backend.providers.schema import GenerationRequest, Message as ProviderMessage, Role as ProviderRole, ProviderType
from backend.core.di import di_container, bootstrap_di

# Dependency Injection Containers
bootstrap_di()
settings = SettingsSystem()
kernel = NovaKernel()
chat = di_container.resolve(ChatSystem)
provider_manager = di_container.resolve(AIProviderManager)
boot_time = time.time()

@asynccontextmanager
async def lifespan(app: FastAPI):
    # Startup Sequence
    app_logger.info("Initializing NOVA Runtime Bootstrap...")
    
    # Load Settings
    await settings.initialize()
    app_logger.info(f"Loaded Settings Profile: {settings.active_profile.profile_id if settings.active_profile else 'None'}")
    
    # Initialize Kernel
    await kernel.startup()
    
    # Initialize Provider Manager
    provider_manager.bootstrap()
    
    # Start Auto-ADB Scanner
    try:
        from backend.devices.core import DeviceManager
        from backend.devices.auto_connect import start_auto_adb
        app.state.zeroconf_tuple = start_auto_adb(DeviceManager())
    except Exception as e:
        app_logger.error(f"Failed to start Auto-ADB: {e}")
    
    app_logger.info(f"NOVA Runtime Successfully Booted in {(time.time() - boot_time) * 1000:.2f}ms")
    app_logger.info(f"Loaded Modules: SettingsSystem, NovaKernel, EventBus, ChatSystem, ProviderManager, AutoADB")
    app_logger.info(f"Version: 1.0.0, Environment: Production")
    
    yield
    
    # Shutdown Sequence
    app_logger.info("Initiating NOVA Runtime Shutdown...")
    try:
        if hasattr(app.state, "zeroconf_tuple"):
            zc, browser = app.state.zeroconf_tuple
            zc.close()
    except Exception:
        pass
    await kernel.shutdown()
    app_logger.info("NOVA Runtime Terminated Gracefully.")

app = FastAPI(title="ADA API", version="1.0.0", lifespan=lifespan)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

@app.get("/health")
async def health_check():
    return {"status": "ok"}

from backend.routers.integrations import router as integrations_router
app.include_router(integrations_router)

@app.get("/auth/{service_id}/callback")
async def oauth_callback(service_id: str, code: str):
    """Mocks the OAuth callback endpoint."""
    from backend.services.api_manager import APIManager
    from fastapi.responses import HTMLResponse
    api_manager = APIManager()
    
    # Store token securely
    api_manager._save_credentials(service_id, "oauth2", access_token=code, refresh_token="mock_refresh", expires_at=time.time() + 3600)
    
    # Return HTML that simulates a quick OAuth flow with premium styling
    return HTMLResponse(f'''
        <html>
            <head>
                <style>
                    body {{
                        background-color: #0f1115;
                        color: white;
                        font-family: system-ui, -apple-system, sans-serif;
                        display: flex;
                        flex-direction: column;
                        align-items: center;
                        justify-content: center;
                        height: 100vh;
                        margin: 0;
                    }}
                    .spinner {{
                        width: 40px;
                        height: 40px;
                        border: 3px solid rgba(255,255,255,0.1);
                        border-radius: 50%;
                        border-top-color: #3b82f6;
                        animation: spin 1s ease-in-out infinite;
                        margin-bottom: 20px;
                    }}
                    @keyframes spin {{
                        to {{ transform: rotate(360deg); }}
                    }}
                </style>
                <script>
                    setTimeout(() => {{
                        document.getElementById('status').innerText = 'Authentication Successful!';
                        document.getElementById('spinner').style.display = 'none';
                        document.getElementById('icon').style.display = 'block';
                        setTimeout(() => window.close(), 1000);
                    }}, 1500);
                </script>
            </head>
            <body>
                <div id="spinner" class="spinner"></div>
                <div id="icon" style="display:none; font-size: 40px; margin-bottom: 20px;">✅</div>
                <h2 id="status" style="font-weight: 500;">Authorizing {service_id.capitalize()}...</h2>
                <p style="color: rgba(255,255,255,0.5); text-align: center; max-width: 300px; line-height: 1.5; font-size: 14px;">
                    Securely connecting with ADA. This window will close automatically.
                </p>
            </body>
        </html>
    ''')

@app.get("/ready")
async def ready_check():
    return {"status": "ready", "kernel_state": kernel.state_manager.current_state}

@app.get("/version")
async def version_check():
    return {"version": "1.0.0", "environment": "production"}

@app.get("/metrics")
async def metrics_check():
    return {
        "kernel": kernel.metrics.model_dump(),
        "settings": settings.metrics.model_dump(),
        "chat": chat.metrics.model_dump()
    }

class ChatPayload(BaseModel):
    content: str
    conversation_id: str = "default"

@app.post("/chat")
async def post_chat(payload: ChatPayload):
    req = KernelRequest(intent=payload.content)
    response = await kernel.dispatch(req)
    res_content = response.content if response.content else f"Echo: {payload.content}"
    msg = ChatMessage(type=ChatMessageType.ASSISTANT, content=res_content)
    await chat.add_message(payload.conversation_id, msg)
    return {"status": "success", "response": res_content}

from fastapi import Request
import io

@app.post("/api/voice/transcribe")
async def voice_transcribe(request: Request):
    audio_bytes = await request.body()
    if not audio_bytes:
        return {"transcript": ""}
        
    app_logger.info(f"Received audio blob: {len(audio_bytes)} bytes for transcription")
    
    # 1. Primary: Groq Whisper-large-v3-turbo (Ultra-fast ~150ms transcription)
    groq_api_key = os.getenv("GROQ_API_KEY", "")
    if groq_api_key:
        try:
            from groq import Groq
            client = Groq(api_key=groq_api_key)
            transcription = client.audio.transcriptions.create(
                file=("audio.webm", audio_bytes),
                model="whisper-large-v3-turbo",
                response_format="json",
                language="en",
                prompt="Ada, WhatsApp, Telegram, Spotify, Settings, Chrome, Windows"
            )
            text = transcription.text.strip()
            app_logger.info(f"Groq Whisper transcription result: {text}")
            return {"transcript": text}
        except Exception as e:
            app_logger.error(f"Groq Whisper transcription error: {e}. Trying Gemini fallback...")

    # 2. Fallback: Google Gemini Audio understanding
    gemini_api_key = os.getenv("GEMINI_API_KEY", "")
    if gemini_api_key:
        try:
            from google import genai
            from google.genai import types
            g_client = genai.Client(api_key=gemini_api_key)
            response = g_client.models.generate_content(
                model='gemini-2.5-flash',
                contents=[
                    types.Part.from_bytes(data=audio_bytes, mime_type="audio/webm"),
                    "Transcribe the user's spoken words verbatim into English text. Output only the transcription, nothing else."
                ]
            )
            text = response.text.strip()
            app_logger.info(f"Gemini Audio transcription result: {text}")
            return {"transcript": text}
        except Exception as ge:
            app_logger.error(f"Gemini transcription error: {ge}")

    return {"transcript": ""}

class ConnectionManager:
    def __init__(self):
        self.active_connections: list[WebSocket] = []

    async def connect(self, websocket: WebSocket):
        await websocket.accept()
        self.active_connections.append(websocket)

    def disconnect(self, websocket: WebSocket):
        if websocket in self.active_connections:
            self.active_connections.remove(websocket)

    async def broadcast(self, message: str):
        for connection in self.active_connections:
            await connection.send_text(message)

chat_ws_manager = ConnectionManager()
events_ws_manager = ConnectionManager()

@app.websocket("/ws/chat")
async def websocket_chat(websocket: WebSocket):
    await chat_ws_manager.connect(websocket)
    
    # Generate dynamic Friday/Jarvis boot greeting
    try:
        from datetime import datetime
        hour = datetime.now().hour
        time_str = "morning" if 5 <= hour < 12 else "afternoon" if 12 <= hour < 17 else "evening" if 17 <= hour < 22 else "night"
        
        greeting = f"System online. Good {time_str}, Boss. ADA is active and all local subroutines are nominal. What are we working on today?"
        
        # Send initial message to frontend
        await websocket.send_json({
            "type": "message_complete",
            "message": {
                "role": "assistant",
                "content": greeting
            }
        })
    except Exception as e:
        app_logger.error(f"Failed to send boot greeting: {e}")

    try:
        while True:
            data = await websocket.receive_text()
            try:
                payload = json.loads(data)
                content = payload.get("content", "")
                conv_id = payload.get("conversation_id", "default")
            except:
                content = data
                conv_id = "default"
                
            # Log User Message
            user_msg = ChatMessage(type=ChatMessageType.USER, content=content)
            await chat.add_message(conv_id, user_msg)
            
            # Dispatch to Kernel for full pipeline processing
            # NO BYPASS. Kernel handles memory, planning, execution, and provider calls.
            req = KernelRequest(user_input=content, conversation_id=conv_id)
            
            ast_msg = ChatMessage(type=ChatMessageType.ASSISTANT, content="")
            await chat.add_message(conv_id, ast_msg)
            
            # Simulate a "thinking" chunk
            await websocket.send_json({
                "type": "message_chunk",
                "message": {
                    "id": ast_msg.message_id,
                    "role": "assistant",
                    "content": "Thinking..."
                }
            })
            
            # Wait for kernel response
            response = await kernel.dispatch(req)
            
            ast_msg.content = response.content if response.content else "Processing complete."
            
            # Finalize message in store
            # The message reference in memory is updated directly
            
            await websocket.send_json({
                "type": "message_complete",
                "message": {
                    "id": ast_msg.message_id,
                    "role": "assistant",
                    "content": ast_msg.content
                }
            })
    except WebSocketDisconnect:
        chat_ws_manager.disconnect(websocket)

@app.websocket("/ws/events")
async def websocket_events(websocket: WebSocket):
    await events_ws_manager.connect(websocket)
    
    async def event_listener(payload, event_type=None):
        try:
            if hasattr(payload, "model_dump"):
                safe_payload = payload.model_dump()
            elif hasattr(payload, "dict"):
                safe_payload = payload.dict()
            else:
                safe_payload = payload if isinstance(payload, dict) else str(payload)

            content = str(safe_payload.get("message", safe_payload.get("content", ""))) if isinstance(safe_payload, dict) else str(safe_payload)
            
            await websocket.send_json({
                "type": event_type.value if event_type else "UNKNOWN",
                "content": content,
                "payload": safe_payload
            })
        except Exception as e:
            import logging
            logging.error(f"Failed to serialize event: {e}")

    # Subscribe to all kernel events by wrapping the callback to include the event_type
    from backend.kernel.events import KernelEventType
    
    # Store listeners to unsubscribe later
    listeners = []
    for et in KernelEventType:
        def make_listener(et_bound):
            async def wrapper(payload):
                await event_listener(payload, event_type=et_bound)
            return wrapper
        listener = make_listener(et)
        listeners.append((et, listener))
        kernel.event_bus.subscribe(et, listener)

    try:
        while True:
            await websocket.receive_text()
    except WebSocketDisconnect:
        events_ws_manager.disconnect(websocket)
        for et, listener in listeners:
            try:
                kernel.event_bus._subscribers[et].remove(listener)
            except ValueError:
                pass

if __name__ == "__main__":
    import uvicorn
    uvicorn.run("backend.main:app", host="0.0.0.0", port=8000, reload=True)
