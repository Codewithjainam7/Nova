import time
from typing import Optional
from backend.browser.schema import BrowserSession, BrowserAction, BrowserPermissionLevel, BrowserMetrics
from backend.browser.adapters import (
    BrowserLauncher, TabManager, NavigationManager, DOMManager, NetworkMonitor,
    DownloadManager, UploadManager, CookieManager, ScreenshotManager, PDFExporter,
    JavaScriptExecutor, HistoryManager, BookmarkManager
)
from backend.browser.dispatcher import BrowserActionQueue, BrowserActionDispatcher, BrowserRecoveryManager, BrowserPermissionManager
from backend.core.logger import app_logger

class BrowserLogger:
    @staticmethod
    def log_action(action: BrowserAction, status: str):
        app_logger.info(f"[BROWSER ACTION - {status}] {action.action_type}")

class BrowserStateManager:
    """Tracks current active tab, URL, loading status."""
    def __init__(self):
        self.active_tab_id: Optional[str] = None
        self.current_url: str = ""

class BrowserManager:
    """Internal orchestration of browser components."""
    def __init__(self, permission_level: BrowserPermissionLevel):
        self.permissions = BrowserPermissionManager(permission_level)
        self.recovery = BrowserRecoveryManager()
        self.queue = BrowserActionQueue()
        self.state = BrowserStateManager()
        
        # Initialize Adapters
        self.launcher = BrowserLauncher()
        self.tab = TabManager()
        self.navigation = NavigationManager()
        self.dom = DOMManager()
        self.network = NetworkMonitor()
        self.download = DownloadManager()
        self.upload = UploadManager()
        self.cookie = CookieManager()
        self.screenshot = ScreenshotManager()
        self.pdf = PDFExporter()
        self.js = JavaScriptExecutor()
        
        registry = {
            "launcher": self.launcher,
            "tab": self.tab,
            "navigation": self.navigation,
            "dom": self.dom,
            "network": self.network,
            "download": self.download,
            "upload": self.upload,
            "cookie": self.cookie,
            "screenshot": self.screenshot,
            "pdf": self.pdf,
            "js": self.js
        }
        self.dispatcher = BrowserActionDispatcher(registry)

class BrowserExecutor:
    """Executes actions safely via the Manager."""
    def __init__(self, manager: BrowserManager, metrics: BrowserMetrics):
        self.manager = manager
        self.metrics = metrics

    async def execute(self, action: BrowserAction):
        start = time.time()
        BrowserLogger.log_action(action, "START")
        
        if not self.manager.permissions.check(action):
            self.metrics.failed_actions += 1
            raise PermissionError(f"Action {action.action_type} denied by permission level {self.manager.permissions.level}")
            
        try:
            success = await self.manager.dispatcher.dispatch(action)
            if success:
                BrowserLogger.log_action(action, "SUCCESS")
                self.metrics.total_actions += 1
        except Exception as e:
            await self.manager.recovery.handle_failure(action, e)
            self.metrics.failed_actions += 1
            raise
        finally:
            elapsed = (time.time() - start) * 1000
            if action.action_type.name == "NAVIGATE":
                self._update_metric("avg_navigation_latency_ms", elapsed)
            elif "CLICK" in action.action_type.name or "TYPE" in action.action_type.name:
                self._update_metric("avg_dom_lookup_latency_ms", elapsed)
            elif "SCREENSHOT" in action.action_type.name:
                self._update_metric("avg_screenshot_latency_ms", elapsed)

    def _update_metric(self, attr: str, elapsed: float):
        n = self.metrics.total_actions
        if n > 0:
            current = getattr(self.metrics, attr)
            new_val = ((current * (n - 1)) + elapsed) / n
            setattr(self.metrics, attr, new_val)

class BrowserEngine:
    """Central entrypoint for Browser Automation."""
    def __init__(self, permission_level: BrowserPermissionLevel = BrowserPermissionLevel.DOWNLOADS_UPLOADS):
        self.metrics = BrowserMetrics()
        self.session = BrowserSession(permissions=permission_level)
        self.manager = BrowserManager(permission_level)
        self.executor = BrowserExecutor(self.manager, self.metrics)

    async def perform_action(self, action: BrowserAction):
        """Public API to request a browser action."""
        await self.executor.execute(action)
