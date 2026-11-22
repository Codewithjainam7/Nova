import asyncio
import time
import json
import sys
import subprocess
from contextlib import asynccontextmanager
from fastapi import FastAPI, WebSocket, WebSocketDisconnect, Response, Request
from fastapi.middleware.cors import CORSMiddleware
from typing import Optional, Dict, Any, List
from pydantic import BaseModel

# Globally guarantee that any subprocess invoked on Windows runs with CREATE_NO_WINDOW
_orig_subprocess_run = subprocess.run
def _silent_subprocess_run(cmd, *args, **kwargs):
    if sys.platform == 'win32' and 'creationflags' not in kwargs:
        kwargs['creationflags'] = 0x08000000
    return _orig_subprocess_run(cmd, *args, **kwargs)
subprocess.run = _silent_subprocess_run

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

    app_logger.info(f"ADA Runtime Successfully Booted in {(time.time() - boot_time) * 1000:.2f}ms")
    app_logger.info(f"Loaded Modules: SettingsSystem, NovaKernel, EventBus, ChatSystem, ProviderManager, AutoADB")
    app_logger.info(f"Version: 1.0.0, Environment: Production")
    
    # Auto-start Cloudflare Remote Tunnel for Mobile Phone access
    try:
        from backend.cloud.tunnel import tunnel_manager
        asyncio.create_task(asyncio.to_thread(tunnel_manager.start_tunnel, 8000))
    except Exception as te:
        app_logger.warning(f"Failed to auto-start Cloudflare tunnel: {te}")
    
    yield
    
    # Shutdown Sequence
    app_logger.info("Initiating ADA Runtime Shutdown...")
    try:
        from backend.cloud.tunnel import tunnel_manager
        tunnel_manager.stop_tunnel()
    except Exception:
        pass
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

from backend.devices.touchpad import router as touchpad_router
app.include_router(touchpad_router)

from backend.cloud.tunnel import router as cloud_router
app.include_router(cloud_router)

from fastapi.responses import HTMLResponse
from backend.cloud.tunnel import get_mobile_hub
app.get("/mobile", response_class=HTMLResponse)(get_mobile_hub)

# Hermes Procedural Skills & Tiered Memory APIs
from backend.capabilities.skill_engine import skill_engine
from backend.memory.tiered_memory import tiered_memory

@app.get("/api/skills")
async def list_skills():
    """Returns list of auto-learned and built-in procedural skills."""
    return {"status": "SUCCESS", "skills": skill_engine.list_skills()}

@app.post("/api/skills/{skill_name}/run")
async def run_skill(skill_name: str, payload: dict = None):
    """Executes a procedural skill."""
    kwargs = payload or {}
    return skill_engine.execute_skill(skill_name, **kwargs)

@app.post("/api/skills/synthesize")
async def synthesize_skill(payload: dict):
    """Synthesizes a new executable skill and stores it in backend/skills/."""
    name = payload.get("name", "")
    code = payload.get("code", "")
    desc = payload.get("description", "")
    return skill_engine.synthesize_skill(name, code, desc)

@app.get("/api/memory/tiered")
async def get_tiered_memory():
    """Returns USER.md and MEMORY.md profiles."""
    return {
        "status": "SUCCESS",
        "user_profile": tiered_memory.read_user_profile(),
        "system_facts": tiered_memory.read_system_facts()
    }

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
    import subprocess
    
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

    # 3. Real GPU Metrics (NVIDIA-SMI)
    gpu_info = {"name": "NVIDIA GeForce RTX 3050 6GB Laptop GPU", "temp": 59, "util": 0}
    try:
        res = subprocess.run(
            ["nvidia-smi", "--query-gpu=name,temperature.gpu,utilization.gpu", "--format=csv,noheader,nounits"],
            capture_output=True, text=True, timeout=1
        )
        if res.returncode == 0 and res.stdout.strip():
            parts = [p.strip() for p in res.stdout.strip().split(",")]
            gpu_info = {
                "name": parts[0],
                "temp": int(float(parts[1])),
                "util": int(float(parts[2]))
            }
    except Exception:
        pass

    # 4. Real Laptop Battery Metrics
    batt = psutil.sensors_battery()
    laptop_batt = {
        "percent": batt.percent if batt else 100,
        "plugged": batt.power_plugged if batt else True
    }

    # 5. Real Display Refresh Rate
    display_info = {"hz": 144, "resolution": "1920x1080"}
    try:
        import win32api
        dm = win32api.EnumDisplaySettings(None, -1)
        display_info = {"hz": dm.DisplayFrequency, "resolution": f"{dm.PelsWidth}x{dm.PelsHeight}"}
    except Exception:
        pass

    # 6. Real Network I/O
    net_info = {"sent_mb": 0.0, "recv_mb": 0.0}
    try:
        net = psutil.net_io_counters()
        net_info = {
            "sent_mb": round(net.bytes_sent / (1024**2), 1),
            "recv_mb": round(net.bytes_recv / (1024**2), 1)
        }
    except Exception:
        pass

    # 7. Real Phone Bridge Metrics (Non-blocking background cache)
    phone_data = getattr(app.state, "_cached_phone_data", {"connected": True, "battery": 80, "device_id": "192.168.0.103:5555"})
    last_phone_check = getattr(app.state, "_last_phone_check", 0)
    now_ts = time.time()
    
    if now_ts - last_phone_check > 15.0:
        app.state._last_phone_check = now_ts
        def _fetch_phone_quick():
            try:
                from backend.devices.core import DeviceManager
                dm = DeviceManager()
                devs = dm.get_connected_devices(auto_discover=False)
                if devs:
                    dev_id = devs[0]
                    b_str = dm.get_battery_level(dev_id)
                    b_num = 80
                    if b_str:
                        m = re.search(r'(\d+)%', str(b_str)) or re.search(r'\b(\d+)\b', str(b_str))
                        if m:
                            b_num = int(m.group(1))
                    return {"connected": True, "battery": b_num, "device_id": dev_id}
            except Exception:
                pass
            return {"connected": False, "battery": None, "device_id": None}

        async def _update_phone_bg():
            res = await asyncio.to_thread(_fetch_phone_quick)
            app.state._cached_phone_data = res

        asyncio.create_task(_update_phone_bg())

    # 8. Active AI Provider & Model
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
        "gpu": gpu_info,
        "laptop_battery": laptop_batt,
        "display": display_info,
        "network": net_info,
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
    content: Optional[str] = None
    message: Optional[str] = None
    conversation_id: str = "default"

    @property
    def text(self) -> str:
        return (self.content or self.message or "").strip()

@app.post("/chat")
@app.post("/api/chat")
async def post_chat(payload: ChatPayload):
    text = payload.text
    if not text:
        return {"status": "error", "response": "Empty message"}
    conv_id = payload.conversation_id or "default"
    
    # Save user message to persistent SQLite
    user_msg = ChatMessage(type=ChatMessageType.USER, content=text)
    await chat.add_message(conv_id, user_msg)
    
    # Broadcast to desktop app WebSocket in real time
    try:
        await chat_ws_manager.broadcast(json.dumps({
            "type": "message_user",
            "message": {
                "id": user_msg.message_id,
                "role": "user",
                "content": text,
                "timestamp": int(time.time() * 1000)
            }
        }))
        await chat_ws_manager.broadcast(json.dumps({
            "type": "message_chunk",
            "message": {
                "id": f"thinking_{int(time.time())}",
                "role": "assistant",
                "content": "Thinking..."
            }
        }))
    except Exception:
        pass

    req = KernelRequest(user_input=text, conversation_id=conv_id)
    response = await kernel.dispatch(req)
    res_content = response.content if response.content else "I've processed your request."
    
    # Save assistant message to persistent SQLite
    ast_msg = ChatMessage(type=ChatMessageType.ASSISTANT, content=res_content)
    await chat.add_message(conv_id, ast_msg)

    # Broadcast completed response to desktop app
    try:
        await chat_ws_manager.broadcast(json.dumps({
            "type": "message_complete",
            "message": {
                "id": ast_msg.message_id,
                "role": "assistant",
                "content": res_content
            }
        }))
    except Exception:
        pass

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
                await chat.update_message(conv_id, ast_msg.message_id, ast_msg.content)
                
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

# -------------------------------------------------------------
# Autonomous Messaging Hub & Dynamic Island Heads-Up Quick-Reply
# -------------------------------------------------------------
@app.get("/api/messaging/active")
async def get_active_message():
    from backend.devices.messaging import messaging_hub
    return {
        "active_message": messaging_hub.active_message.dict() if messaging_hub.active_message else None
    }

@app.post("/api/messaging/incoming")
async def receive_incoming_message(payload: dict):
    from backend.devices.messaging import messaging_hub
    sender = payload.get("sender", "Unknown")
    platform = payload.get("platform", "whatsapp")
    message = payload.get("message", "")
    suggested_reply = payload.get("suggested_reply")

    msg = await messaging_hub.receive_message(
        sender=sender,
        platform=platform,
        message=message,
        suggested_reply=suggested_reply,
        events_manager=events_ws_manager
    )
    return {"status": "success", "data": msg.dict()}

@app.post("/api/messaging/simulate")
async def simulate_incoming_message(payload: dict = None):
    from backend.devices.messaging import messaging_hub
    payload = payload or {}
    sender = payload.get("sender", "Devisri")
    platform = payload.get("platform", "whatsapp")
    message = payload.get("message", "Hey! Are you free for the meeting right now?")
    suggested_reply = payload.get("suggested_reply")

    msg = await messaging_hub.receive_message(
        sender=sender,
        platform=platform,
        message=message,
        suggested_reply=suggested_reply,
        events_manager=events_ws_manager
    )
    return {"status": "success", "simulated": True, "data": msg.dict()}

@app.post("/api/messaging/reply")
async def reply_incoming_message(payload: dict):
    from backend.devices.messaging import messaging_hub
    reply_text = payload.get("reply_text", "")
    message_id = payload.get("message_id")
    res = await messaging_hub.send_reply(
        reply_text=reply_text,
        message_id=message_id,
        events_manager=events_ws_manager
    )
    return res

@app.post("/api/messaging/dismiss")
async def dismiss_incoming_message(payload: dict = None):
    from backend.devices.messaging import messaging_hub
    payload = payload or {}
    message_id = payload.get("message_id")
    res = await messaging_hub.dismiss_message(
        message_id=message_id,
        events_manager=events_ws_manager
    )
    return res

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

class SeekPayload(BaseModel):
    position: float

@app.post("/api/system/media/seek")
async def seek_system_media(payload: SeekPayload):
    """Seeks track to specified position in seconds via GSMTC."""
    from backend.island.media_controller import system_media_controller
    res = await system_media_controller.seek(payload.position)
    return {"success": res, "position": payload.position}

class VolumePayload(BaseModel):
    volume: float

@app.get("/api/system/volume")
async def get_system_volume():
    """Returns current Windows system master volume (0-100)."""
    from backend.island.media_controller import system_media_controller
    vol = system_media_controller.get_system_volume()
    return {"success": True, "volume": vol}

@app.post("/api/system/volume")
async def set_system_volume(payload: VolumePayload):
    """Sets Windows system master volume (0-100)."""
    from backend.island.media_controller import system_media_controller
    res = system_media_controller.set_system_volume(payload.volume)
    return {"success": res, "volume": payload.volume}

