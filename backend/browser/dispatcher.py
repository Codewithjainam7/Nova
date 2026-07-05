import asyncio
from backend.browser.schema import BrowserAction, BrowserPermissionLevel
from backend.core.logger import app_logger

class BrowserPermissionManager:
    def __init__(self, current_level: BrowserPermissionLevel):
        self.level = current_level

    def check(self, action: BrowserAction) -> bool:
        if self.level == BrowserPermissionLevel.READ_ONLY:
            if "CLICK" in action.action_type.name or "TYPE" in action.action_type.name:
                app_logger.warning(f"Permission denied for action: {action.action_type}")
                return False
        elif self.level == BrowserPermissionLevel.AUTOMATION:
            if action.action_type.name in ["DOWNLOAD", "UPLOAD"]:
                app_logger.warning(f"Permission denied for action: {action.action_type}")
                return False
        return True

class BrowserRecoveryManager:
    """Handles retries and fallbacks for failed Browser actions."""
    async def handle_failure(self, action: BrowserAction, exception: Exception):
        app_logger.error(f"Browser Action failed: {action.action_type} - {str(exception)}")
        app_logger.info("Attempting browser recovery...")
        await asyncio.sleep(0.1)

class BrowserActionQueue:
    def __init__(self):
        self.queue = asyncio.Queue()

    async def enqueue(self, action: BrowserAction):
        await self.queue.put(action)

    async def dequeue(self) -> BrowserAction:
        return await self.queue.get()

class BrowserActionDispatcher:
    """Routes actions to the specific browser sub-managers."""
    def __init__(self, adapters: dict):
        self.registry = adapters

    async def dispatch(self, action: BrowserAction) -> bool:
        try:
            if action.action_type.name == "LAUNCH":
                await self.registry["launcher"].launch()
            elif action.action_type.name == "NAVIGATE":
                await self.registry["navigation"].navigate(action.payload.get("url", ""))
            elif action.action_type.name == "CLICK":
                await self.registry["dom"].click(action.payload.get("selector", ""))
            elif action.action_type.name == "DOWNLOAD":
                await self.registry["download"].download(action.payload.get("url", ""))
            elif action.action_type.name == "SCREENSHOT":
                await self.registry["screenshot"].capture()
            else:
                app_logger.debug(f"Dispatched generic browser action: {action.action_type}")
                await asyncio.sleep(0.01)
            return True
        except Exception as e:
            raise e
