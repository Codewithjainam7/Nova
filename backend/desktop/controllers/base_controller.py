import time
import subprocess
from typing import Optional, Dict, Type
from backend.core.logger import app_logger

try:
    from pywinauto import Application
except ImportError:
    Application = None
    app_logger.warning("pywinauto not found, generic UIA will fail.")

class AppController:
    """Base interface for all application controllers."""
    def is_open(self) -> bool:
        raise NotImplementedError
        
    def launch(self):
        raise NotImplementedError
        
    def wait_ready(self, timeout: int = 10) -> bool:
        raise NotImplementedError
        
    def execute(self, intent: str, entity: Optional[str]) -> bool:
        raise NotImplementedError


class GenericUIController(AppController):
    """Fallback controller using pywinauto's UIA backend to inspect the accessibility tree."""
    def __init__(self, exe_name: str, window_title_re: Optional[str] = None):
        self.exe_name = exe_name
        self.title_re = window_title_re or f".*{exe_name}.*"
        self.app = None

    def is_open(self) -> bool:
        if not Application:
            return False
        try:
            Application(backend="uia").connect(title_re=self.title_re, timeout=0.5)
            return True
        except Exception:
            return False

    def launch(self):
        app_map = {
            "windows settings": "ms-settings:",
            "settings": "ms-settings:",
            "calculator": "calc.exe",
            "notepad": "notepad.exe",
            "spotify": "spotify.exe"
        }
        target = app_map.get(self.exe_name.lower(), self.exe_name)
        
        try:
            if target.startswith("ms-") or target.startswith("http"):
                import os
                os.startfile(target)
                return
            subprocess.Popen(target)
        except Exception as e:
            app_logger.error(f"Failed to launch {target}: {e}")
            import os
            try:
                os.startfile(target)
            except Exception as e2:
                app_logger.error(f"Failed to startfile {target}: {e2}")

    def wait_ready(self, timeout: int = 10) -> bool:
        if not Application:
            return False
        for _ in range(timeout):
            if self.is_open():
                try:
                    self.app = Application(backend="uia").connect(title_re=self.title_re, timeout=1)
                    return True
                except Exception:
                    pass
            time.sleep(1)
        return False

    def execute(self, intent: str, entity: Optional[str]) -> bool:
        if not self.app:
            if not self.wait_ready(timeout=2):
                return False
                
        try:
            win = self.app.top_window()
            win.set_focus()
            
            if intent == "open_app":
                return True
                
            elif intent == "search" and entity:
                edits = win.descendants(control_type="Edit")
                if edits:
                    edits[0].click_input()
                    edits[0].type_keys(entity, with_spaces=True)
                    win.type_keys("{ENTER}")
                    return True
                    
            elif intent == "play_media" and entity:
                # If they ask to play a specific media item, try searching for it first
                edits = win.descendants(control_type="Edit")
                if edits:
                    edits[0].click_input()
                    edits[0].type_keys(entity, with_spaces=True)
                    win.type_keys("{ENTER}")
                    time.sleep(2)
                    win.type_keys("{TAB}{TAB}{ENTER}")
                    return True
                    
            elif intent == "click_button" and entity:
                btns = win.descendants(control_type="Button", title_re=f".*{entity}.*")
                if btns:
                    btns[0].click_input()
                    return True
                    
            return False
        except Exception as e:
            app_logger.error(f"GenericUIController execute failed: {e}")
            return False
