import asyncio
from backend.core.logger import app_logger

class ClipboardManager:
    async def read_text(self) -> str:
        app_logger.debug("Read from clipboard")
        await asyncio.sleep(0.01)
        return "mock clipboard text"

    async def write_text(self, text: str):
        app_logger.debug(f"Wrote to clipboard: {text}")
        await asyncio.sleep(0.01)

class ScreenshotManager:
    async def capture_screen(self) -> bytes:
        app_logger.info("Captured full screen screenshot")
        await asyncio.sleep(0.05)
        return b"mock_png_data"

class FilesystemManager:
    async def read_file(self, path: str) -> str:
        app_logger.debug(f"FS read: {path}")
        await asyncio.sleep(0.01)
        return "mock file content"

class ProcessManager:
    async def get_processes(self) -> list:
        app_logger.debug("Process list retrieved")
        await asyncio.sleep(0.05)
        return ["explorer.exe", "nova.exe"]

class MonitorManager:
    async def get_monitors(self) -> list:
        app_logger.debug("Monitor list retrieved")
        return [{"id": 1, "resolution": "1920x1080"}]

class NotificationManager:
    async def show_notification(self, title: str, message: str):
        app_logger.info(f"System Notification: {title} - {message}")

class ShortcutManager:
    pass # Managed partly by KeyboardController
