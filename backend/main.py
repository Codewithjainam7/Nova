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
    
    app_logger.info(f"NOVA Runtime Successfully Booted in {(time.time() - boot_time) * 1000:.2f}ms")
    app_logger.info(f"Loaded Modules: SettingsSystem, NovaKernel, EventBus, ChatSystem, ProviderManager")
    app_logger.info(f"Version: 1.0.0, Environment: Production")
    
    yield
    
    # Shutdown Sequence
    app_logger.info("Initiating NOVA Runtime Shutdown...")
    await kernel.shutdown()
    app_logger.info("NOVA Runtime Terminated Gracefully.")

app = FastAPI(title="NOVA API", version="1.0.0", lifespan=lifespan)

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
    # The kernel currently returns a Mocked response from MockProvider due to sleep.
    # In the mock phase, response content might be empty if we don't have a real pipeline returning string.
    # We will simulate a basic response if empty for the sake of the bootstrap.
    res_content = response.content if response.content else f"Echo: {payload.content}"
    msg = ChatMessage(type=ChatMessageType.ASSISTANT, content=res_content)
    await chat.add_message(payload.conversation_id, msg)
    return {"status": "success", "response": res_content}

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
            req = KernelRequest(user_input=content)
            
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
            await websocket.send_json({
                "type": event_type.value if event_type else "UNKNOWN",
                "content": str(payload.get("message", "")) if isinstance(payload, dict) else str(payload),
                "payload": payload
            })
        except Exception:
            pass

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
    uvicorn.run("main:app", host="0.0.0.0", port=8000, reload=True)
