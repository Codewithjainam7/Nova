import time
import subprocess
import os
import ctypes
from typing import Optional, Dict, Type
from backend.core.logger import app_logger
import uiautomation as auto

def _ensure_desktop():
    try:
        user32 = ctypes.windll.user32
        h_default = user32.OpenDesktopW("Default", 0, False, 0x01FF)
        if h_default:
            user32.SetThreadDesktop(h_default)
    except Exception:
        pass

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
    """Fallback controller using native UIAutomation to inspect and navigate any desktop app."""
    def __init__(self, exe_name: str, window_title_re: Optional[str] = None):
        self.exe_name = exe_name
        self.title_query = window_title_re or exe_name
        self.window: Optional[auto.WindowControl] = None

    def _find_window(self) -> Optional[auto.WindowControl]:
        _ensure_desktop()
        root = auto.GetRootControl()
        target = self.title_query.lower()
        for child in root.GetChildren():
            name = child.Name.lower()
            if target in name or (child.ClassName and target in child.ClassName.lower()):
                return child
        return None

    def is_open(self) -> bool:
        return self._find_window() is not None

    def launch(self):
        _ensure_desktop()
        app_map = {
            "windows settings": "ms-settings:",
            "settings": "ms-settings:",
            "calculator": "calculator:",
            "calc": "calculator:",
            "notepad": "notepad.exe",
            "spotify": "spotify:",
            "whatsapp": "whatsapp:",
            "explorer": "explorer.exe",
            "brave": "brave.exe",
            "chrome": "chrome.exe",
            "edge": "msedge.exe",
            "taskmgr": "taskmgr.exe"
        }
        target = app_map.get(self.exe_name.lower(), self.exe_name)
        app_logger.info(f"GenericUIController: Launching target '{target}'")
        
        try:
            os.startfile(target)
        except Exception as e:
            app_logger.warning(f"Failed os.startfile for {target}: {e}. Trying subprocess.")
            try:
                si = subprocess.STARTUPINFO()
                si.lpDesktop = r"WinSta0\Default"
                subprocess.Popen([target], startupinfo=si)
            except Exception as e2:
                app_logger.error(f"Failed subprocess launch for {target}: {e2}")

    def wait_ready(self, timeout: int = 10) -> bool:
        _ensure_desktop()
        start = time.time()
        while time.time() - start < timeout:
            win = self._find_window()
            if win:
                self.window = win
                return True
            time.sleep(0.5)
        return False

    def execute(self, intent: str, entity: Optional[str]) -> bool:
        _ensure_desktop()
        win = self._find_window()
        if not win:
            if not self.wait_ready(timeout=3):
                return False
            win = self._find_window()
            
        try:
            win.SetActive()
            time.sleep(0.2)
            
            intent = intent.lower().strip()
            
            if intent in ["open_app", "launch", "focus"]:
                return True
                
            elif intent in ["search", "find"] and entity:
                # Look for an Edit/Search box
                edits = win.GetChildren()
                target_edit = None
                for c in edits:
                    if c.ControlTypeName in ["EditControl", "DocumentControl"] or "search" in (c.Name or "").lower():
                        target_edit = c
                        break
                if not target_edit:
                    target_edit = win.EditControl(searchDepth=5)
                    
                if target_edit and target_edit.Exists(0, 0):
                    target_edit.SetFocus()
                    time.sleep(0.1)
                    auto.SendKeys(f"{{Ctrl}}a{entity}{{ENTER}}")
                    return True
                else:
                    # Fallback to direct window key injection
                    win.SendKeys(f"{entity}{{ENTER}}")
                    return True
                    
            elif intent == "play_media" and entity:
                win.SendKeys(f"{{Ctrl}}l{entity}{{ENTER}}")
                time.sleep(1.5)
                win.SendKeys("{ENTER}")
                return True
                
            elif intent in ["click_button", "click"] and entity:
                btn = win.ButtonControl(searchDepth=5, Name=entity)
                if not btn.Exists(0, 0):
                    # Try partial match
                    for child in win.GetChildren():
                        if entity.lower() in (child.Name or "").lower():
                            btn = child
                            break
                if btn and btn.Exists(0, 0):
                    btn.Click()
                    return True
                    
            elif intent in ["type", "type_text"] and entity:
                auto.SendKeys(entity)
                return True
                
            elif intent == "close_app":
                win.SendKeys("{Alt}{F4}")
                return True
                
            return False
        except Exception as e:
            app_logger.error(f"GenericUIController execution failed: {e}")
            return False
