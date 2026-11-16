import asyncio
import time
import json
from contextlib import asynccontextmanager
from fastapi import FastAPI, WebSocket, WebSocketDisconnect, Response, Request
from fastapi.middleware.cors import CORSMiddleware
from typing import Optional, Dict, Any, List
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
    app_logger.info("Initializing ADA Runtime Bootstrap...")
    
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

    # Start Autonomous "Hey ADA" Wake Word Engine
    try:
        from backend.voice.wake_word import WakeWordService
        loop = asyncio.get_running_loop()

        async def _async_wake_detected(wake_phrase: str, directive: str, oral_text: str):
            await events_ws_manager.broadcast(json.dumps({
                "type": "WAKE_WORD_DETECTED",
                "wake_phrase": wake_phrase,
                "directive": directive,
                "oral_response": oral_text
            }))

        async def _async_listening_state(msg: str):
            if msg == "idle":
                await events_ws_manager.broadcast(json.dumps({
                    "type": "RESPONSE_COMPLETED"
                }))
            else:
                await events_ws_manager.broadcast(json.dumps({
                    "type": "WAKE_WORD_LISTENING",
                    "message": msg
                }))

        async def _async_directive_ready(directive_text: str):
            if not directive_text or not str(directive_text).strip():
                return
            directive_clean = str(directive_text).strip()
            conv_id = "default"
            app_logger.info(f"[WakeWord Dispatch] Executing directive: '{directive_clean}'")

            user_msg = ChatMessage(type=ChatMessageType.USER, content=directive_clean)
            await chat.add_message(conv_id, user_msg)
            await chat_ws_manager.broadcast(json.dumps({
                "type": "message_user",
                "message": {
                    "id": user_msg.message_id,
                    "role": "user",
                    "content": directive_clean,
                    "timestamp": int(time.time() * 1000)
                }
            }))

            ast_msg = ChatMessage(type=ChatMessageType.ASSISTANT, content="")
            await chat.add_message(conv_id, ast_msg)
            await chat_ws_manager.broadcast(json.dumps({
                "type": "message_chunk",
                "message": {
                    "id": ast_msg.message_id,
                    "role": "assistant",
                    "content": "Thinking..."
                }
            }))

            try:
                req = KernelRequest(user_input=directive_clean, conversation_id=conv_id)
                res = await kernel.dispatch(req)
                ast_content = res.content if res and res.content else "Directive completed, Boss."
            except Exception as ke:
                app_logger.error(f"[WakeWord Dispatch] Kernel error: {ke}")
                ast_content = f"Encountered an issue executing that command: {str(ke)}"

            ast_msg.content = ast_content
            await chat_ws_manager.broadcast(json.dumps({
                "type": "message_complete",
                "message": {
                    "id": ast_msg.message_id,
                    "role": "assistant",
                    "content": ast_content
                }
            }))

        def _sync_wake(w: str, d: str, o: str):
            asyncio.run_coroutine_threadsafe(_async_wake_detected(w, d, o), loop)

        def _sync_listening_state(msg: str):
            asyncio.run_coroutine_threadsafe(_async_listening_state(msg), loop)

        def _sync_directive(d: str):
            asyncio.run_coroutine_threadsafe(_async_directive_ready(d), loop)

        wake_service = WakeWordService(
            on_wake_detected=_sync_wake,
            on_listening_state=_sync_listening_state,
            on_directive_ready=_sync_directive
        )
        wake_service.start()
        app.state.wake_service = wake_service
        app_logger.info("Autonomous Wake Word Listener Engine successfully initialized and active.")
    except Exception as e:
        app_logger.error(f"Failed to start Wake Word Engine: {e}")

    # Start Autonomous Call Screening Telephony Guardian
    try:
        from backend.devices.call_screening import call_screener
        loop_cs = asyncio.get_running_loop()

        def _on_call_event(event_data: dict):
            try:
                asyncio.run_coroutine_threadsafe(
                    events_ws_manager.broadcast(json.dumps({
                        "type": "CALL_SCREENING_EVENT",
                        **event_data
                    })),
                    loop_cs
                )
            except Exception as ce:
                app_logger.debug(f"Call event broadcast notice: {ce}")

        call_screener.register_callback(_on_call_event)
        app.state.call_screen_task = asyncio.create_task(call_screener.start_monitoring())
        app_logger.info("Autonomous Mobile Telephony Guardian initialized.")
    except Exception as e:
        app_logger.error(f"Failed to start Call Screening: {e}")
    
    app_logger.info(f"ADA Runtime Successfully Booted in {(time.time() - boot_time) * 1000:.2f}ms")
    app_logger.info(f"Loaded Modules: SettingsSystem, NovaKernel, EventBus, ChatSystem, ProviderManager, AutoADB")
    app_logger.info(f"Version: 1.0.0, Environment: Production")
    
    yield
    
    # Shutdown Sequence
    app_logger.info("Initiating ADA Runtime Shutdown...")
    try:
        if hasattr(app.state, "zeroconf_tuple"):
            zc, browser = app.state.zeroconf_tuple
            zc.close()
    except Exception:
        pass
    try:
        if hasattr(app.state, "wake_service") and app.state.wake_service:
            app.state.wake_service.stop()
    except Exception:
        pass
    try:
        if hasattr(app.state, "call_screen_task"):
            from backend.devices.call_screening import call_screener
            call_screener.stop_monitoring()
            app.state.call_screen_task.cancel()
    except Exception:
        pass
    await kernel.shutdown()
    app_logger.info("ADA Runtime Terminated Gracefully.")

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

@app.get("/api/telemetry")
async def get_system_telemetry():
    """Returns accurate real-time hardware telemetry and ADB phone bridge stats."""
    import psutil
    import os
    import re
    
    # 1. Real CPU Metrics
    per_cpu = psutil.cpu_percent(percpu=True)
    total_cpu = round(sum(per_cpu) / len(per_cpu), 1) if per_cpu else psutil.cpu_percent()
    logical_cores = psutil.cpu_count(logical=True) or 16
    physical_cores = psutil.cpu_count(logical=False) or 10
    
    cpu_freq = psutil.cpu_freq()
    freq_ghz = round(cpu_freq.current / 1000.0, 2) if cpu_freq else 2.40
    
    # 2. Real RAM Metrics
    vm = psutil.virtual_memory()
    ram_total_gb = round(vm.total / (1024**3), 1)
    ram_used_gb = round(vm.used / (1024**3), 1)
    ram_percent = vm.percent

    # 3. Real Phone Bridge Metrics
    phone_data = {"connected": False, "battery": None, "device_id": None}
    try:
        from backend.devices.core import DeviceManager
        dm = DeviceManager()
        devices = dm.get_connected_devices()
        if devices:
            dev_id = devices[0]
            batt_str = dm.get_battery_level(dev_id)
            batt_num = None
            if batt_str:
                m = re.search(r'(\d+)%', str(batt_str)) or re.search(r'\b(\d+)\b', str(batt_str))
                if m:
                    batt_num = int(m.group(1))
            phone_data = {
                "connected": True,
                "battery": batt_num,
                "device_id": dev_id
            }
    except Exception as e:
        app_logger.debug(f"Telemetry phone query: {e}")

    # 4. Active AI Provider & Model
    active_provider = "GROQ"
    active_model = "LLAMA 3.3 70B"
    try:
        if hasattr(provider_manager, "primary_provider") and provider_manager.primary_provider:
            active_provider = str(provider_manager.primary_provider).upper()
        p_obj = provider_manager.get_active_provider()
        if hasattr(p_obj, "model") and p_obj.model:
            active_model = str(p_obj.model).upper()
    except Exception:
        pass

    return {
        "status": "ok",
        "cpu": {
            "percent": total_cpu,
            "per_cpu": per_cpu,
            "threads": logical_cores,
            "cores": physical_cores,
            "freq_ghz": freq_ghz
        },
        "memory": {
            "total_gb": ram_total_gb,
            "used_gb": ram_used_gb,
            "percent": ram_percent
        },
        "phone": phone_data,
        "ai": {
            "provider": active_provider,
            "model": active_model
        }
    }

@app.get("/api/memory/profile")
async def get_memory_profile():
    """Returns the persistent profile graph, social contacts, rules, and habit statistics."""
    from backend.memory.profile_store import profile_store
    from backend.memory.routine_tracker import routine_tracker
    return {
        "status": "ok",
        "profile": profile_store.get_profile(),
        "routine": routine_tracker.get_routine_stats(),
        "active_context": routine_tracker.get_routine_context()
    }

class ContactUpsertPayload(BaseModel):
    name: str
    alias: Optional[str] = None
    platform: Optional[str] = None
    notes: Optional[str] = None

@app.post("/api/memory/profile/contact")
async def upsert_contact_endpoint(payload: ContactUpsertPayload):
    from backend.memory.profile_store import profile_store
    profile_store.upsert_contact(payload.name, payload.alias, payload.platform, payload.notes)
    return {"status": "ok", "message": f"Contact '{payload.name}' updated successfully."}

@app.get("/api/missions")
async def get_missions():
    """Returns list of all autonomous background and overnight missions."""
    from backend.missions.mission_runner import MissionRunner
    runner = MissionRunner(provider_manager)
    return {"status": "ok", "missions": runner.get_all_missions()}

@app.get("/api/missions/{mission_id}")
async def get_mission_detail(mission_id: str):
    """Returns the full report content and details of a specific mission."""
    from backend.missions.mission_runner import MissionRunner
    runner = MissionRunner(provider_manager)
    m = runner.get_mission_by_id(mission_id)
    if not m:
        return {"status": "error", "message": "Mission not found."}
    
    report_file = m.get("report_file")
    content = ""
    if report_file and os.path.exists(report_file):
        try:
            with open(report_file, "r", encoding="utf-8") as f:
                content = f.read()
        except Exception:
            content = "Failed to read report file."
            
    return {"status": "ok", "mission": m, "content": content}

@app.get("/api/briefing")
async def get_briefing_endpoint(boot: bool = False):
    """Generates a dynamic, time-aware and mission-aware Jarvis executive briefing."""
    from backend.proactive.briefing import BriefingEngine
    engine = BriefingEngine(provider_manager)
    if boot:
        briefing = await engine.generate_boot_briefing()
    else:
        briefing = await engine.generate_comprehensive_briefing()
    return {"status": "ok", "briefing": briefing}

class MissionRunPayload(BaseModel):
    query: str

@app.post("/api/missions/run")
async def run_mission_endpoint(payload: MissionRunPayload):
    """Triggers an autonomous mission immediately."""
    from backend.missions.mission_runner import MissionRunner
    runner = MissionRunner(provider_manager)
    result = await runner.execute_mission(payload.query)
    return {"status": "ok", "mission": result}

class ChatPayload(BaseModel):
    content: str
    conversation_id: str = "default"

@app.post("/chat")
async def post_chat(payload: ChatPayload):
    req = KernelRequest(user_input=payload.content, conversation_id=payload.conversation_id)
    response = await kernel.dispatch(req)
    res_content = response.content if response.content else f"Echo: {payload.content}"
    msg = ChatMessage(type=ChatMessageType.ASSISTANT, content=res_content)
    await chat.add_message(payload.conversation_id, msg)
    return {"status": "success", "response": res_content}

@app.get("/api/tts")
@app.post("/api/tts")
async def api_tts(
    request: Request,
    text: Optional[str] = None,
    voice: Optional[str] = None
):
    """
    ADA V2 Studio Neural Voice Synthesizer
    Generates and streams studio-grade natural speech matching the Ada V2 voice pack (nazirlouis/ada_v2).
    Default: 'en-GB-SoniaNeural' (ADA's signature witty British studio persona).
    """
    content_text = text or ""
    if not content_text and request.method == "POST":
        try:
            body = await request.json()
            content_text = body.get("text", "")
            voice = voice or body.get("voice")
        except Exception:
            try:
                raw_bytes = await request.body()
                content_text = raw_bytes.decode('utf-8')
            except Exception:
                pass
                
    content_text = content_text.replace("*", "").replace("#", "").replace("`", "").strip()
    if not content_text:
        return Response(status_code=400, content="Missing text")
        
    target_voice = voice or os.getenv("ADA_VOICE", "en-GB-SoniaNeural")
    
    wake_service = getattr(request.app.state, "wake_service", None)
    if wake_service:
        wake_service.set_speaking(True)

    try:
        import edge_tts
        communicate = edge_tts.Communicate(content_text, target_voice)
        audio_chunks = []
        async for chunk in communicate.stream():
            if chunk["type"] == "audio":
                audio_chunks.append(chunk["data"])
        
        if audio_chunks:
            if wake_service:
                async def _unmute():
                    await asyncio.sleep(1.5)
                    wake_service.set_speaking(False)
                asyncio.create_task(_unmute())

            return Response(
                content=b"".join(audio_chunks),
                media_type="audio/mpeg",
                headers={
                    "Cache-Control": "public, max-age=3600",
                    "X-ADA-Voice": target_voice
                }
            )
    except Exception as e:
        app_logger.error(f"[API TTS] Error generating speech: {e}")
        
    return Response(status_code=500, content="TTS synthesis failed")

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
                language="en"
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
    
    # Generate dynamic Friday/Jarvis boot briefing
    try:
        from backend.proactive.briefing import BriefingEngine
        briefing_engine = BriefingEngine(provider_manager)
        greeting = await briefing_engine.generate_boot_briefing()
        
        # Send initial message to frontend
        await websocket.send_json({
            "type": "message_complete",
            "is_greeting": True,
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
                try:
                    payload = json.loads(data)
                    content = payload.get("content", "")
                    conv_id = payload.get("conversation_id", "default")
                except Exception:
                    content = data
                    conv_id = "default"
                    
                if not content or not str(content).strip():
                    continue
                    
                # Log User Message
                user_msg = ChatMessage(type=ChatMessageType.USER, content=str(content))
                await chat.add_message(conv_id, user_msg)
                
                # Dispatch to Kernel for full pipeline processing
                req = KernelRequest(user_input=str(content), conversation_id=conv_id)
                
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
                
                await websocket.send_json({
                    "type": "message_complete",
                    "message": {
                        "id": ast_msg.message_id,
                        "role": "assistant",
                        "content": ast_msg.content
                    }
                })
            except WebSocketDisconnect:
                raise
            except Exception as e:
                app_logger.error(f"Error processing chat message: {e}", exc_info=True)
                try:
                    await websocket.send_json({
                        "type": "message_complete",
                        "message": {
                            "role": "assistant",
                            "content": f"Encountered an issue executing that command: {str(e)}"
                        }
                    })
                except Exception:
                    break
    except WebSocketDisconnect:
        chat_ws_manager.disconnect(websocket)
    except Exception as e:
        app_logger.error(f"WebSocket unhandled error: {e}")
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
            except (ValueError, KeyError):
                pass
    except Exception as e:
        app_logger.error(f"WebSocket events error: {e}")
        events_ws_manager.disconnect(websocket)
        for et, listener in listeners:
            try:
                kernel.event_bus._subscribers[et].remove(listener)
            except (ValueError, KeyError):
                pass

if __name__ == "__main__":
    import uvicorn
    uvicorn.run("backend.main:app", host="0.0.0.0", port=8000, reload=True)

@app.get("/api/voice/wake/status")
async def get_wake_status():
    wake_service = getattr(app.state, "wake_service", None)
    if wake_service:
        return wake_service.status()
    return {"running": False, "speaking": False}

@app.post("/api/voice/wake/toggle")
async def toggle_wake_status():
    wake_service = getattr(app.state, "wake_service", None)
    if wake_service:
        if wake_service.is_running:
            wake_service.stop()
        else:
            wake_service.start()
        return wake_service.status()
    return {"running": False}

@app.get("/api/devices/call-screening/status")
async def get_call_screening_status():
    from backend.devices.call_screening import call_screener
    return {
        "enabled": call_screener.enabled,
        "is_monitoring": call_screener.is_monitoring,
        "unattended_seconds": call_screener.unattended_seconds,
        "current_call_state": call_screener.current_state,
        "active_caller": call_screener.active_caller_name
    }

@app.post("/api/devices/call-screening/toggle")
async def toggle_call_screening():
    from backend.devices.call_screening import call_screener
    call_screener.enabled = not call_screener.enabled
    return {
        "enabled": call_screener.enabled,
        "status": "ACTIVE" if call_screener.enabled else "STANDBY"
    }

@app.get("/api/devices/call-screening/logs")
async def get_call_screening_logs():
    from backend.devices.call_screening import call_screener
    records = []
    if os.path.exists(call_screener.log_file):
        try:
            with open(call_screener.log_file, "r", encoding="utf-8") as f:
                records = json.load(f)
        except Exception:
            records = []
    return {"logs": records}

@app.get("/api/system/media/current")
async def get_current_system_media():
    """Returns currently playing media metadata (track, artist, thumbnail, duration) via GSMTC."""
    from backend.island.media_controller import system_media_controller
    media = await system_media_controller.get_current_media()
    return {"success": True, "media": media}

class MediaControlPayload(BaseModel):
    action: str  # toggle, next, prev

@app.post("/api/system/media/control")
async def control_system_media(payload: MediaControlPayload):
    """Executes media playback control (toggle play/pause, next, previous)."""
    from backend.island.media_controller import system_media_controller
    act = (payload.action or "").lower().strip()
    result = False
    if act in ["toggle", "play", "pause"]:
        result = await system_media_controller.toggle_play_pause()
    elif act in ["next", "skip"]:
        result = await system_media_controller.skip_next()
    elif act in ["prev", "previous"]:
        result = await system_media_controller.skip_previous()
    return {"success": result, "action": act}

