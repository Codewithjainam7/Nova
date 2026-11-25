"""
ADA Local Windows Worker Daemon (Hybrid Cloud <-> Laptop Bridge).
Connects your Windows PC outbound to a 24/7 Cloud ADA Brain over WebSocket,
receiving desktop/wallpaper/winget/ADB tasks whenever your laptop is powered on.

Usage:
    set ADA_CLOUD_WS_URL=wss://your-cloud-host.example.com/ws/worker
    set ADA_WORKER_TOKEN=your-secret-token
    python scripts/local_worker_agent.py
"""

import asyncio
import json
import os
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from backend.core.di import bootstrap_di, di_container
from backend.core.logger import app_logger
from backend.browser.core import BrowserEngine
from backend.desktop.core import DesktopEngine
from backend.devices.core import DeviceManager
from backend.kernel.capability_router import CapabilityRouter
from backend.planner.schema import Task
from backend.providers.native_windows import NativeWindowsProvider


async def _handle_task(router: CapabilityRouter, payload: dict) -> dict:
    try:
        task_data = payload.get("task", {})
        task = Task(**task_data)
        ok = await router.route_task(task)
        return {
            "type": "TASK_RESULT",
            "request_id": payload.get("request_id"),
            "success": bool(ok),
            "output": task.action_metadata.get("execution_output", "Completed on Windows worker."),
        }
    except Exception as e:
        return {
            "type": "TASK_RESULT",
            "request_id": payload.get("request_id"),
            "success": False,
            "output": str(e),
        }


async def run_worker():
    import websockets

    ws_url = os.getenv("ADA_CLOUD_WS_URL", "ws://127.0.0.1:8000/ws/worker").strip()
    token = os.getenv("ADA_WORKER_TOKEN", "").strip()
    if token and "token=" not in ws_url:
        sep = "&" if "?" in ws_url else "?"
        ws_url = f"{ws_url}{sep}token={token}"

    bootstrap_di()
    router = CapabilityRouter(
        api_manager=None,
        browser_engine=di_container.resolve(BrowserEngine),
        desktop_engine=di_container.resolve(DesktopEngine),
        native_engine=NativeWindowsProvider(),
        device_manager=DeviceManager(),
    )

    while True:
        try:
            app_logger.info(f"[LocalWorker] Connecting to cloud brain: {ws_url}")
            async with websockets.connect(ws_url, ping_interval=20, ping_timeout=20) as ws:
                app_logger.info("[LocalWorker] Connected and ready for remote tasks.")
                async for raw in ws:
                    msg = json.loads(raw)
                    if msg.get("type") == "TASK_EXECUTE":
                        result = await _handle_task(router, msg)
                        await ws.send(json.dumps(result))
        except Exception as e:
            app_logger.warning(f"[LocalWorker] Connection lost ({e}); retrying in 5s...")
            await asyncio.sleep(5)


if __name__ == "__main__":
    asyncio.run(run_worker())
