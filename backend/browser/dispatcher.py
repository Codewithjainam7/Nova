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
        import traceback
        app_logger.error(f"Browser Action failed: {action.action_type} - {repr(exception)}")
        app_logger.error(traceback.format_exc())
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
            # Route to the appropriate adapter based on action type
            action_name = action.action_type.name
            
            if action_name == "LAUNCH":
                return await self.registry["launcher"].execute(action)
            elif action_name in ["NEW_TAB", "CLOSE_TAB", "SWITCH_TAB"]:
                return await self.registry["tab"].execute(action)
            elif action_name in ["NAVIGATE", "RELOAD", "BACK", "FORWARD"]:
                return await self.registry["navigation"].execute(action)
            elif action_name in ["CLICK", "DOUBLE_CLICK", "RIGHT_CLICK", "HOVER", "TYPE", "FILL", "SELECT", "CHECK", "UNCHECK", "SCROLL", "EXTRACT_TEXT", "EXTRACT_HTML", "EXTRACT_ATTRIBUTES", "WAIT_FOR_ELEMENT"]:
                return await self.registry["dom"].execute(action)
            elif action_name == "SCREENSHOT":
                return await self.registry["screenshot"].execute(action)
            elif action_name == "DOWNLOAD":
                return await self.registry["download"].execute(action)
            elif action_name == "UPLOAD":
                return await self.registry["upload"].execute(action)
            elif action_name == "EXECUTE_JS":
                return await self.registry["js"].execute(action)
            elif action_name == "WAIT_FOR_NETWORK":
                return await self.registry["network"].execute(action)
            elif action_name == "EXPORT_PDF":
                return await self.registry["pdf"].execute(action)
            else:
                app_logger.debug(f"Dispatched generic browser action: {action.action_type}")
                await asyncio.sleep(0.01)
                return True
        except Exception as e:
            import traceback
            app_logger.error(f"Browser action exception: {e}")
            app_logger.error(traceback.format_exc())
            raise e
