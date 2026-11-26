from typing import Dict, Any, Optional
from backend.desktop.controllers.base_controller import AppController, GenericUIController
from backend.desktop.controllers.spotify_controller import SpotifyController
from backend.desktop.controllers.settings_controller import SettingsController
from backend.desktop.controllers.calculator_controller import CalculatorController
from backend.desktop.controllers.notepad_controller import NotepadController
from backend.desktop.controllers.file_explorer_controller import FileExplorerController
from backend.desktop.controllers.software_controller import SoftwareInstallerController
from backend.desktop.controllers.media_controller import MediaWallpaperController
from backend.desktop.controllers.terminal_controller import TerminalWorkspaceController
from backend.core.logger import app_logger

class AppActionRouter:
    """Routes semantic intents to the appropriate application controller."""
    
    def __init__(self):
        self.calculator = CalculatorController()
        self.notepad = NotepadController()
        self.file_explorer = FileExplorerController()
        self.spotify = SpotifyController()
        self.settings = SettingsController()
        self.installer = SoftwareInstallerController()
        self.media = MediaWallpaperController()
        self.terminal = TerminalWorkspaceController()
        
        self.registry: Dict[str, AppController] = {
            "spotify": self.spotify,
            "settings": self.settings,
            "windows settings": self.settings,
            "calculator": self.calculator,
            "calc": self.calculator,
            "notepad": self.notepad,
            "note": self.notepad,
            "explorer": self.file_explorer,
            "file explorer": self.file_explorer,
            "files": self.file_explorer,
            "installer": self.installer,
            "software": self.installer,
            "winget": self.installer,
            "package_manager": self.installer,
            "install": self.installer,
            "download": self.installer,
            "media": self.media,
            "wallpaper": self.media,
            "images": self.media,
            "photos": self.media,
            "terminal": self.terminal,
            "powershell": self.terminal,
            "cmd": self.terminal,
            "workspace": self.terminal,
        }
        self.last_output: Optional[str] = None
        self.last_file_path: Optional[str] = None
        
    def _get_generic_exe(self, app_name: str) -> str:
        app_map = {
            "calculator": "calculator:",
            "calc": "calculator:",
            "notepad": "notepad.exe",
            "paint": "mspaint.exe",
            "wordpad": "write.exe",
            "explorer": "explorer.exe",
            "browser": "msedge.exe",
            "spotify": "spotify:",
            "settings": "ms-settings:",
            "whatsapp": "whatsapp:",
            "brave": "brave.exe",
            "chrome": "chrome.exe",
            "edge": "msedge.exe"
        }
        return app_map.get(app_name.lower(), app_name)

    def execute(self, app_name: str, intent: str, entity: str) -> bool:
        app_name_lower = app_name.lower().strip()
        self.last_output = None
        self.last_file_path = None
        
        # 1. Look for specific dedicated controller
        controller = self.registry.get(app_name_lower)
        
        # 2. Fallback to Generic UIA Controller
        if not controller:
            exe_name = self._get_generic_exe(app_name_lower)
            controller = GenericUIController(exe_name, app_name_lower)
            
        app_logger.info(f"Routing intent '{intent}' for '{app_name}' to {controller.__class__.__name__}")
        
        # 3. Ensure app is open and ready (skip for headless operations like folder organizing, installer, media, and terminal)
        headless_intents = {
            "organize", "organize_folder", "sort_folder", "clean_folder",
            "delete_files", "delete_file", "delete_screenshots", "remove_files", "clear_files", "delete", "remove",
            "install_software", "download_and_install", "install", "download",
            "find_wallpaper", "set_wallpaper", "find_images", "download_wallpaper",
            "create_collage", "make_collage",
            "create_workspace", "create_folder", "open_vscode", "system_diagnostics", "run_command"
        }
        if intent.lower().strip() not in headless_intents:
            if not controller.is_open():
                app_logger.info(f"App {app_name} is not open, launching...")
                controller.launch()
                if not controller.wait_ready(timeout=10):
                    app_logger.error(f"Failed to launch or attach to {app_name}")
                    return False
                
        # 4. Execute the intent
        success = controller.execute(intent, entity)
        
        # 5. Extract output and generated file path if available
        if hasattr(controller, 'last_file_path') and controller.last_file_path:
            self.last_file_path = controller.last_file_path
        if hasattr(controller, 'last_output') and controller.last_output:
            self.last_output = controller.last_output
        elif hasattr(controller, 'last_result') and controller.last_result:
            self.last_output = controller.last_result
        elif hasattr(controller, 'last_content') and controller.last_content:
            self.last_output = controller.last_content
            
        return success
