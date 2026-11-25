"""
Remote Windows Worker Relay for Hybrid Cloud <-> Local Execution.
Allows ADA running 24/7 in cloud mode to offload desktop/device tasks over an authenticated
WebSocket connection when the user's Windows laptop is awake, and gracefully report offline
status when the laptop is shut down.
"""

import asyncio
import json
import uuid
from typing import Optional, Dict, Any
from fastapi import WebSocket
from backend.core.logger import app_logger


class RemoteWorkerRelay:
    """Manages active outbound WebSocket connections from local Windows ADA agents."""

    def __init__(self):
        self._worker_ws: Optional[WebSocket] = None
        self._pending: Dict[str, asyncio.Future] = {}
        self._lock = asyncio.Lock()

    def is_connected(self) -> bool:
        return self._worker_ws is not None

    async def register(self, websocket: WebSocket):
        async with self._lock:
            self._worker_ws = websocket
        app_logger.info("[RemoteWorkerRelay] Windows worker connected to cloud brain.")

    async def unregister(self, websocket: WebSocket):
        async with self._lock:
            if self._worker_ws is websocket:
                self._worker_ws = None
        # Fail any pending futures cleanly
        for req_id, fut in list(self._pending.items()):
            if not fut.done():
                fut.set_result({"success": False, "output": "Windows laptop worker disconnected."})
            self._pending.pop(req_id, None)
        app_logger.info("[RemoteWorkerRelay] Windows worker disconnected.")

    def resolve_response(self, msg: Dict[str, Any]):
        req_id = msg.get("request_id")
        if req_id and req_id in self._pending:
            fut = self._pending.pop(req_id)
            if not fut.done():
                fut.set_result(msg)

    async def dispatch_task(self, task_dict: Dict[str, Any], timeout: float = 30.0) -> Dict[str, Any]:
        if not self._worker_ws:
            return {
                "success": False,
                "offline": True,
                "output": "Your Windows laptop is currently offline/shut down, so desktop actions are paused until it wakes up. Cloud research, briefings, and AI tasks remain online 24/7.",
            }

        req_id = str(uuid.uuid4())
        loop = asyncio.get_running_loop()
        fut: asyncio.Future = loop.create_future()
        self._pending[req_id] = fut

        try:
            await self._worker_ws.send_text(
                json.dumps({"type": "TASK_EXECUTE", "request_id": req_id, "task": task_dict})
            )
            return await asyncio.wait_for(fut, timeout=timeout)
        except asyncio.TimeoutError:
            self._pending.pop(req_id, None)
            return {"success": False, "output": "Windows worker timed out executing desktop task."}
        except Exception as e:
            self._pending.pop(req_id, None)
            return {"success": False, "output": f"Worker relay error: {e}"}


remote_worker_relay = RemoteWorkerRelay()
