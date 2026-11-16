import time
import os
import ctypes
from typing import Optional
from backend.desktop.controllers.base_controller import AppController
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

class NotepadController(AppController):
    """
    Dedicated controller for Windows Notepad.
    Handles launching, writing text, reading document contents, saving, and closing.
    """

    def __init__(self):
        self.last_content: Optional[str] = None

    def _get_notepad_window(self) -> Optional[auto.WindowControl]:
        _ensure_desktop()
        root = auto.GetRootControl()
        for child in root.GetChildren():
            try:
                name = (child.Name or "").lower()
                cls = child.ClassName or ""
                if "notepad" in name or cls == "Notepad":
                    return child
            except Exception:
                continue
        return None

    def _get_editor_control(self, win: auto.WindowControl) -> Optional[auto.Control]:
        # In Windows 11, the text editor is RichEditD2DPT / DocumentControl
        # In legacy Windows, it's EditControl
        doc = win.DocumentControl(searchDepth=5)
        if doc.Exists(0, 0):
            return doc
        edit = win.EditControl(searchDepth=5)
        if edit.Exists(0, 0):
            return edit
        return None

    def is_open(self) -> bool:
        return self._get_notepad_window() is not None

    def launch(self):
        _ensure_desktop()
        app_logger.info("Launching Windows Notepad...")
        try:
            # Modern Windows 11 AppX launch
            os.system('explorer.exe shell:AppsFolder\\Microsoft.WindowsNotepad_8wekyb3d8bbwe!App')
        except Exception as e:
            app_logger.warning(f"shell:AppsFolder launch failed: {e}. Falling back to notepad.exe.")
            try:
                os.startfile("notepad.exe")
            except Exception as e2:
                app_logger.error(f"Failed to launch Notepad: {e2}")

    def wait_ready(self, timeout: int = 10) -> bool:
        _ensure_desktop()
        start = time.time()
        while time.time() - start < timeout:
            win = self._get_notepad_window()
            if win:
                editor = self._get_editor_control(win)
                if editor and editor.Exists(0, 0):
                    return True
            time.sleep(0.5)
        return False

    def write_text(self, text: str, append: bool = False) -> bool:
        _ensure_desktop()
        win = self._get_notepad_window()
        if not win:
            raise RuntimeError("Notepad window is not open.")
            
        win.SetActive()
        time.sleep(0.2)
        editor = self._get_editor_control(win)
        if not editor:
            raise RuntimeError("Could not find text editor control in Notepad.")
            
        editor.SetFocus()
        time.sleep(0.1)
        
        # Try setting value directly via ValuePattern first
        try:
            pattern = editor.GetValuePattern()
            if append:
                curr = pattern.Value or ""
                pattern.SetValue(curr + ("\n" if curr else "") + text)
            else:
                pattern.SetValue(text)
            self.last_content = text
            app_logger.info(f"NotepadController: Text set successfully via ValuePattern.")
            return True
        except Exception:
            pass
            
        # Fallback to keystroke injection
        if not append:
            auto.SendKeys("{Ctrl}a{Delete}")
            time.sleep(0.1)
            
        # Send text in chunks for stability
        auto.SendKeys(text)
        self.last_content = text
        return True

    def read_text(self) -> str:
        _ensure_desktop()
        win = self._get_notepad_window()
        if not win:
            return ""
        editor = self._get_editor_control(win)
        if not editor:
            return ""
            
        try:
            val = editor.GetValuePattern().Value
            self.last_content = val
            return val
        except Exception:
            pass
            
        val = editor.Name or ""
        self.last_content = val
        return val

    def save_file(self, file_path: str) -> bool:
        _ensure_desktop()
        win = self._get_notepad_window()
        if not win:
            return False
            
        win.SetActive()
        time.sleep(0.2)
        win.SendKeys("{Ctrl}s")
        time.sleep(0.8)
        
        # Look for Save As dialog
        save_dlg = win.WindowControl(searchDepth=3, Name="Save as") or auto.WindowControl(searchDepth=2, Name="Save as")
        if save_dlg.Exists(2, 1):
            file_name_edit = save_dlg.EditControl(searchDepth=5, AutomationId="FileNameControlHost") or save_dlg.EditControl(searchDepth=5)
            if file_name_edit.Exists(1, 1):
                file_name_edit.SendKeys(f"{{Ctrl}}a{file_path}{{ENTER}}")
                time.sleep(0.5)
                return True
                
        return False

    def execute(self, intent: str, entity: Optional[str]) -> bool:
        _ensure_desktop()
        win = self._get_notepad_window()
        if not win:
            if not self.wait_ready(timeout=3):
                return False
            win = self._get_notepad_window()

        intent = intent.lower().strip()
        
        if intent in ["open_app", "launch"]:
            if win:
                win.SetActive()
            return True
            
        elif intent in ["write_note", "type_text", "write", "note", "type"] and entity:
            return self.write_text(entity)
            
        elif intent in ["append_note", "append"] and entity:
            return self.write_text(entity, append=True)
            
        elif intent in ["read_text", "read", "get_text"]:
            res = self.read_text()
            return bool(res)
            
        elif intent in ["save_file", "save"] and entity:
            return self.save_file(entity)
            
        elif intent in ["clear", "delete_all"]:
            editor = self._get_editor_control(win)
            if editor:
                editor.SetFocus()
                auto.SendKeys("{Ctrl}a{Delete}")
                return True
                
        return False
