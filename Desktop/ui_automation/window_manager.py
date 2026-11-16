import uiautomation as auto
from typing import List, Optional
import time
import ctypes

from .exceptions import WindowNotFoundError, MultipleWindowsFoundError, AccessDeniedError
from .logger import UILogger
from .models import WindowInfo
import psutil

def _ensure_default_desktop():
    try:
        user32 = ctypes.windll.user32
        h_default = user32.OpenDesktopW("Default", 0, False, 0x01FF)
        if h_default:
            user32.SetThreadDesktop(h_default)
    except Exception:
        pass

class WindowManager:
    """Manages discovery and state of top-level windows."""
    
    def __init__(self):
        # Ensure interactive desktop access
        _ensure_default_desktop()
        # Set global search timeout
        auto.uiautomation.SetGlobalSearchTimeout(1)

    def find_window(self, title: str = None, partial_title: str = None, 
                    process: str = None, class_name: str = None, 
                    automation_id: str = None, timeout: float = 3.0) -> auto.WindowControl:
        """Finds a window based on search criteria."""
        _ensure_default_desktop()
        search_params = {
            "title": title, "partial_title": partial_title, 
            "process": process, "class_name": class_name, "automation_id": automation_id
        }
        UILogger.log_search("Window", search_params, False)
        
        start_time = time.time()
        while (time.time() - start_time) < timeout:
            windows = self.list_windows()
            matches = []
            
            for win in windows:
                if title and win.Name != title:
                    continue
                if partial_title and partial_title.lower() not in (win.Name or "").lower():
                    continue
                if class_name and win.ClassName != class_name:
                    continue
                if automation_id and win.AutomationId != automation_id:
                    continue
                
                # Check process name if provided
                if process:
                    try:
                        p = psutil.Process(win.ProcessId)
                        if p.name().lower() != process.lower():
                            continue
                    except Exception:
                        continue
                
                matches.append(win)
                
            if len(matches) == 1:
                UILogger.log_search("Window", search_params, True)
                return matches[0]
            elif len(matches) > 1:
                # Return the first match rather than failing catastrophically
                UILogger.log_search("Window", search_params, True)
                return matches[0]
                
            time.sleep(0.5)

        UILogger.error(f"Window not found: {search_params}")
        raise WindowNotFoundError(f"Could not find window matching {search_params} within {timeout}s")

    def list_windows(self) -> List[auto.WindowControl]:
        """Lists all top-level windows."""
        _ensure_default_desktop()
        windows = []
        root = auto.GetRootControl()
        for child in root.GetChildren():
            try:
                if isinstance(child, auto.WindowControl) or child.ControlTypeName in ['WindowControl', 'PaneControl']:
                    name = child.Name
                    if name and name.strip():
                        windows.append(child)
            except Exception:
                continue
        return windows

    def activate_window(self, window: auto.WindowControl) -> bool:
        """Brings the window to the foreground."""
        _ensure_default_desktop()
        try:
            window.SetActive()
            window.SetTopmost(True)
            time.sleep(0.1)
            window.SetTopmost(False)
            return True
        except Exception as e:
            UILogger.error("Failed to activate window", exc_info=True)
            return False

    def close_window(self, window: auto.WindowControl) -> bool:
        """Closes the window."""
        _ensure_default_desktop()
        try:
            window.GetWindowPattern().Close()
            return True
        except Exception as e:
            try:
                # Fallback to Alt+F4 or click close button
                window.SendKeys('{Alt}{F4}')
                return True
            except:
                UILogger.error("Failed to close window", exc_info=True)
                return False
                
    def get_active_window(self) -> Optional[auto.WindowControl]:
        """Returns the currently active window."""
        _ensure_default_desktop()
        try:
            return auto.GetFocusedControl().GetTopLevelControl()
        except:
            return None
