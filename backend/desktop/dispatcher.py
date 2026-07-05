import asyncio
from backend.desktop.schema import DesktopAction, DesktopPermissionLevel
from backend.core.logger import app_logger

class DesktopPermissionManager:
    def __init__(self, current_level: DesktopPermissionLevel):
        self.level = current_level

    def check(self, action: DesktopAction) -> bool:
        # Dummy logic for permissions
        if self.level == DesktopPermissionLevel.READ_ONLY:
            # Prevent destructive actions
            if any(keyword in action.action_type.name for keyword in ["WRITE", "DELETE", "CREATE", "RENAME", "MOVE"]):
                app_logger.warning(f"Permission denied for action: {action.action_type}")
                return False
        return True

class DesktopRecoveryManager:
    """Handles retries and fallbacks for failed OS actions."""
    async def handle_failure(self, action: DesktopAction, exception: Exception):
        app_logger.error(f"Action failed: {action.action_type} - {str(exception)}")
        # Dummy recovery (e.g. retry once)
        app_logger.info("Attempting recovery / retry...")
        await asyncio.sleep(0.1)

class DesktopActionQueue:
    def __init__(self):
        self.queue = asyncio.Queue()

    async def enqueue(self, action: DesktopAction):
        await self.queue.put(action)

    async def dequeue(self) -> DesktopAction:
        return await self.queue.get()

class DesktopActionDispatcher:
    """Routes actions to the specific hardware/OS controllers."""
    def __init__(self, controllers_and_managers: dict):
        self.registry = controllers_and_managers

    async def dispatch(self, action: DesktopAction) -> bool:
        # Simplistic dispatch mapping for prototype
        try:
            action_name = action.action_type.name
            
            if action_name in ["MOUSE_MOVE", "MOUSE_CLICK", "MOUSE_DRAG", "MOUSE_SCROLL"]:
                return await self.registry["mouse"].execute(action)
            elif action_name in ["APP_LAUNCH", "APP_CLOSE", "APP_FIND"]:
                return await self.registry["app"].execute(action)
            elif action_name in ["WINDOW_MINIMIZE", "WINDOW_MAXIMIZE", "WINDOW_RESTORE", "WINDOW_MOVE", "WINDOW_RESIZE", "WINDOW_FOCUS"]:
                return await self.registry["window"].execute(action)
            elif action_name in ["KEYBOARD_TYPE", "KEYBOARD_SHORTCUT"]:
                return await self.registry["keyboard"].execute(action)
            elif action_name in ["CLIPBOARD_READ", "CLIPBOARD_WRITE"]:
                return await self.registry["clipboard"].execute(action)
            elif action_name == "SCREENSHOT":
                return await self.registry["screenshot"].execute(action)
            elif action_name.startswith("FS_"):
                return await self.registry["fs"].execute(action)
            else:
                app_logger.debug(f"Dispatched generic action: {action.action_type}")
                await asyncio.sleep(0.01)
                return True

        except Exception as e:
            raise e
