import uiautomation as auto
from typing import List, Optional
import time

from .exceptions import WindowNotFoundError, MultipleWindowsFoundError, AccessDeniedError
from .logger import UILogger
from .models import WindowInfo
import psutil

class WindowManager:
    """Manages discovery and state of top-level windows."""
    
    def __init__(self):
        # Set global search timeout
        auto.uiautomation.SetGlobalSearchTimeout(1)

    def find_window(self, title: str = None, partial_title: str = None, 
                    process: str = None, class_name: str = None, 
                    automation_id: str = None, timeout: float = 3.0) -> auto.WindowControl:
        """Finds a window based on search criteria."""
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
                if partial_title and partial_title.lower() not in win.Name.lower():
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
                UILogger.error(f"Multiple windows found for criteria: {search_params}")
                raise MultipleWindowsFoundError(f"Found {len(matches)} windows.")
                
            time.sleep(0.5)

        UILogger.error(f"Window not found: {search_params}")
        raise WindowNotFoundError(f"Could not find window matching {search_params} within {timeout}s")

    def list_windows(self) -> List[auto.WindowControl]:
        """Lists all top-level windows."""
        windows = []
        root = auto.GetRootControl()
        for child in root.GetChildren():
            if isinstance(child, auto.WindowControl) or child.ControlTypeName == 'WindowControl':
                windows.append(child)
        return windows

    def activate_window(self, window: auto.WindowControl) -> bool:
        """Brings the window to the foreground."""
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
        try:
            return auto.GetFocusedControl().GetTopLevelControl()
        except:
            return None
