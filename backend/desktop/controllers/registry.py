from typing import Dict, Any
from backend.desktop.controllers.base_controller import AppController, GenericUIController
from backend.desktop.controllers.spotify_controller import SpotifyController
from backend.desktop.controllers.settings_controller import SettingsController
from backend.core.logger import app_logger

class AppActionRouter:
    """Routes semantic intents to the appropriate application controller."""
    
    def __init__(self):
        self.registry: Dict[str, AppController] = {
            "spotify": SpotifyController(),
            "settings": SettingsController(),
            "windows settings": SettingsController(),
            # "browser": BrowserController()
        }
        
    def _get_generic_exe(self, app_name: str) -> str:
        app_map = {
            "calculator": "calc",
            "notepad": "notepad",
            "paint": "mspaint",
            "wordpad": "write",
            "explorer": "explorer",
            "browser": "msedge",
            "spotify": "spotify:",
            "settings": "ms-settings:",
            "whatsapp": "whatsapp:",
            "brave": "brave",
            "chrome": "chrome",
            "edge": "msedge"
        }
        return app_map.get(app_name.lower(), app_name)

    def execute(self, app_name: str, intent: str, entity: str) -> bool:
        app_name_lower = app_name.lower()
        
        # 1. Look for specific tier A/B controller
        controller = self.registry.get(app_name_lower)
        
        # 2. Fallback to Tier B Generic UIA Controller
        if not controller:
            exe_name = self._get_generic_exe(app_name_lower)
            # Capitalize first letter for window titles usually
            title_re = f".*{app_name.title()}.*|.*{app_name.lower()}.*|.*{app_name.upper()}.*"
            controller = GenericUIController(exe_name, title_re)
            
        app_logger.info(f"Routing intent '{intent}' for '{app_name}' to {controller.__class__.__name__}")
        
        # 3. Ensure app is open and ready
        if not controller.is_open():
            app_logger.info(f"App {app_name} is not open, launching...")
            controller.launch()
            if not controller.wait_ready(timeout=10):
                app_logger.error(f"Failed to launch or attach to {app_name}")
                return False
                
        # 4. Execute the intent
        return controller.execute(intent, entity)
