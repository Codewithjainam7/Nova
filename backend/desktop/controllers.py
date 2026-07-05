import asyncio
from backend.core.logger import app_logger

class MouseController:
    async def move(self, x: int, y: int):
        app_logger.debug(f"Mouse moved to {x}, {y}")
        await asyncio.sleep(0.01)

    async def click(self, button: str = "left"):
        app_logger.debug(f"Mouse clicked: {button}")
        await asyncio.sleep(0.01)
        
    async def scroll(self, amount: int):
        app_logger.debug(f"Mouse scrolled: {amount}")
        await asyncio.sleep(0.01)

class KeyboardController:
    async def type_text(self, text: str):
        app_logger.debug(f"Keyboard typing: {text}")
        await asyncio.sleep(0.01)

    async def shortcut(self, keys: list):
        app_logger.debug(f"Keyboard shortcut: {'+'.join(keys)}")
        await asyncio.sleep(0.01)

class WindowManager:
    async def focus(self, window_id: str):
        app_logger.debug(f"Focused window: {window_id}")
        await asyncio.sleep(0.02)

    async def resize(self, window_id: str, width: int, height: int):
        app_logger.debug(f"Resized window {window_id} to {width}x{height}")
        await asyncio.sleep(0.02)

class ApplicationManager:
    async def launch(self, app_path: str):
        app_logger.info(f"Launched application: {app_path}")
        await asyncio.sleep(0.1)

    async def close(self, app_name: str):
        app_logger.info(f"Closed application: {app_name}")
        await asyncio.sleep(0.1)
