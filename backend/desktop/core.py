import time
from typing import Optional
from backend.desktop.schema import DesktopSession, DesktopAction, DesktopPermissionLevel, DesktopMetrics
from backend.desktop.windows_adapters import (
    WindowsApplicationManager, WindowsWindowManager, WindowsMouseController,
    WindowsKeyboardController, WindowsClipboardManager, WindowsScreenshotManager,
    WindowsFilesystemManager, WindowsProcessManager, WindowsIntentManager
)
from backend.desktop.dispatcher import DesktopActionQueue, DesktopActionDispatcher, DesktopRecoveryManager, DesktopPermissionManager
from backend.core.logger import app_logger

class DesktopLogger:
    @staticmethod
    def log_action(action: DesktopAction, status: str):
        payload_str = str(action.payload)
        if len(payload_str) > 100:
            payload_str = payload_str[:97] + "..."
        app_logger.info(f"[DESKTOP ACTION - {status}] {action.action_type} | Payload: {payload_str}")

class DesktopStateManager:
    """Tracks current UI state, window positions, active monitor, etc."""
    def __init__(self):
        self.active_window: Optional[str] = None

class DesktopManager:
    """Internal orchestration of desktop automation."""
    def __init__(self, permission_level: DesktopPermissionLevel):
        self.permissions = DesktopPermissionManager(permission_level)
        self.recovery = DesktopRecoveryManager()
        self.queue = DesktopActionQueue()
        self.state = DesktopStateManager()
        
        # Initialize Controllers
        self.mouse = WindowsMouseController()
        self.keyboard = WindowsKeyboardController()
        self.window = WindowsWindowManager()
        self.app = WindowsApplicationManager()
        self.clipboard = WindowsClipboardManager()
        self.screenshot = WindowsScreenshotManager()
        self.fs = WindowsFilesystemManager()
        self.process = WindowsProcessManager()
        self.intent = WindowsIntentManager()
        
        # Wire Dispatcher
        registry = {
            "mouse": self.mouse,
            "keyboard": self.keyboard,
            "window": self.window,
            "app": self.app,
            "clipboard": self.clipboard,
            "screenshot": self.screenshot,
            "fs": self.fs,
            "process": self.process,
            "intent": self.intent
        }
        self.dispatcher = DesktopActionDispatcher(registry)

class DesktopExecutor:
    """Executes actions safely via the Manager."""
    def __init__(self, manager: DesktopManager, metrics: DesktopMetrics):
        self.manager = manager
        self.metrics = metrics

    async def execute(self, action: DesktopAction):
        start = time.time()
        DesktopLogger.log_action(action, "START")
        
        # 1. Permission Check
        if not self.manager.permissions.check(action):
            self.metrics.failed_actions += 1
            raise PermissionError(f"Action {action.action_type} denied by permission level {self.manager.permissions.level}")
            
        # 2. Dispatch with Retries and Verification
        max_retries = action.payload.get("retries", 3)
        attempt = 0
        success = False
        last_error = None
        
        try:
            while attempt < max_retries and not success:
                try:
                    success = await self.manager.dispatcher.dispatch(action)
                    
                    # Vision/OCR Verification fallback if native hooks fail
                    if success and action.payload.get("verify_ocr"):
                        expected_text = action.payload.get("verify_ocr")
                        # Placeholder for actual Vision API call
                        app_logger.info(f"[OCR Verification] Verifying screen contains: {expected_text}")
                        # if expected_text not in ocr_result: raise VerificationError
                        
                    if success:
                        DesktopLogger.log_action(action, "SUCCESS")
                        self.metrics.total_actions += 1
                    else:
                        raise RuntimeError(f"Dispatcher returned False for {action.action_type}")
                except Exception as e:
                    last_error = e
                    attempt += 1
                    app_logger.warning(f"Desktop Action failed (Attempt {attempt}/{max_retries}): {e}")
                    if attempt < max_retries:
                        import asyncio
                        await self.manager.recovery.handle_failure(action, e)
                        await asyncio.sleep(1) # Backoff
                    else:
                        self.metrics.failed_actions += 1
                        raise RuntimeError(f"Desktop action failed after {max_retries} attempts. Last error: {e}")
                        
        finally:
            elapsed = (time.time() - start) * 1000
            # Basic metric routing based on type
            if "MOUSE" in action.action_type.name:
                self._update_metric("avg_mouse_latency_ms", elapsed)
            elif "KEYBOARD" in action.action_type.name:
                self._update_metric("avg_keyboard_latency_ms", elapsed)
            elif "SCREENSHOT" in action.action_type.name:
                self._update_metric("avg_screenshot_latency_ms", elapsed)

    def _update_metric(self, attr: str, elapsed: float):
        n = self.metrics.total_actions
        if n > 0:
            current = getattr(self.metrics, attr)
            new_val = ((current * (n - 1)) + elapsed) / n
            setattr(self.metrics, attr, new_val)

    def _launch_app(self, action: DesktopAction):
        app_name = action.payload.get("app_name")
        if not app_name:
            raise ValueError("No app_name provided in Desktop Action payload")

        # Map common names to Windows executables
        app_map = {
            "calculator": "calc",
            "notepad": "notepad",
            "paint": "mspaint",
            "wordpad": "write",
            "explorer": "explorer",
            "browser": "msedge"
        }
        exe_name = app_map.get(app_name.lower(), app_name)

        try:
            # os.startfile is Windows only
            os.startfile(exe_name)
        except Exception as e:
            app_logger.error(f"Failed to launch {exe_name}: {e}")
            raise

class DesktopEngine:
    """Central entrypoint for Desktop Automation."""
    def __init__(self, permission_level: DesktopPermissionLevel = DesktopPermissionLevel.AUTOMATION):
        self.metrics = DesktopMetrics()
        self.session = DesktopSession(permissions=permission_level)
        self.manager = DesktopManager(permission_level)
        self.executor = DesktopExecutor(self.manager, self.metrics)

    async def perform_action(self, action: DesktopAction):
        """Public API to request a desktop action."""
        await self.executor.execute(action)
