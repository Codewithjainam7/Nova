import asyncio
import os
import shutil
import psutil
import time
from typing import Any
from backend.core.logger import app_logger
from backend.desktop.schema import DesktopAction, DesktopActionType

try:
    import pywinauto
    import pyautogui
    import pyperclip
    import win32api
    import win32gui
    import win32con
except ImportError:
    app_logger.warning("Windows automation libraries not found. Desktop Engine will fail.")

class WindowsApplicationManager:
    async def execute(self, action: DesktopAction) -> Any:
        app_name_or_path = action.payload.get("path") or action.payload.get("name")
        if action.action_type == DesktopActionType.APP_LAUNCH:
            if not app_name_or_path:
                raise ValueError("App path or name required for APP_LAUNCH")
            
            def _launch():
                # Map common names to Windows executables
                app_map = {
                    "calculator": "calc",
                    "notepad": "notepad",
                    "paint": "mspaint",
                    "wordpad": "write",
                    "explorer": "explorer",
                    "browser": "msedge",
                    "spotify": "spotify:",
                    "settings": "ms-settings:",
                    "task manager": "taskmgr",
                    "recycle bin": "shell:RecycleBinFolder",
                    "whatsapp": "whatsapp:",
                    "brave": "brave",
                    "chrome": "chrome",
                    "edge": "msedge",
                    "firefox": "firefox"
                }
                exe_name = app_name_or_path
                for key, mapped_name in app_map.items():
                    if key in app_name_or_path.lower():
                        exe_name = mapped_name
                        break
                
                app_logger.info(f"WindowsApplicationManager: app_name_or_path={app_name_or_path}, mapped to exe_name={exe_name}")

                # We use subprocess/os.startfile or pywinauto
                # os.startfile is non-blocking and works well for generic paths
                try:
                    app_logger.info(f"Trying os.startfile({exe_name})")
                    os.startfile(exe_name)
                    app_logger.info("os.startfile succeeded")
                except Exception as e:
                    app_logger.warning(f"os.startfile failed: {e}. Falling back to pywinauto.")
                    # fallback to pywinauto if it's an exe that needs hooking
                    pywinauto.Application(backend="uia").start(exe_name)
            
            await asyncio.to_thread(_launch)
            # Give the app time to open and focus before subsequent actions (like typing)
            await asyncio.sleep(3.5)
            return True
            
        elif action.action_type == DesktopActionType.APP_CLOSE:
            if not app_name_or_path:
                raise ValueError("App name required for APP_CLOSE")
            
            def _close():
                for proc in psutil.process_iter(['name']):
                    if app_name_or_path.lower() in proc.info['name'].lower():
                        proc.terminate()
            
            await asyncio.to_thread(_close)
            return True
        return False

class WindowsWindowManager:
    async def execute(self, action: DesktopAction) -> Any:
        window_title = action.payload.get("title")
        if not window_title:
            return False
            
        def _find_window():
            try:
                # connect to the window by title regex
                app = pywinauto.Desktop(backend="uia")
                dlg = app.window(title_re=f".*{window_title}.*")
                return dlg
            except Exception as e:
                app_logger.error(f"Window not found: {e}")
                return None
                
        def _manage():
            dlg = _find_window()
            if not dlg:
                return False
                
            if action.action_type == DesktopActionType.WINDOW_MINIMIZE:
                dlg.minimize()
            elif action.action_type == DesktopActionType.WINDOW_MAXIMIZE:
                dlg.maximize()
            elif action.action_type == DesktopActionType.WINDOW_RESTORE:
                dlg.restore()
            elif action.action_type == DesktopActionType.WINDOW_FOCUS:
                dlg.set_focus()
            elif action.action_type == DesktopActionType.WINDOW_MOVE:
                x, y = action.payload.get("x", 0), action.payload.get("y", 0)
                # pywinauto expects rect or move
                pass # Skipping exact resize/move logic for brevity unless requested
            return True
            
        return await asyncio.to_thread(_manage)

class WindowsMouseController:
    async def execute(self, action: DesktopAction) -> Any:
        x = action.payload.get("x")
        y = action.payload.get("y")
        
        def _mouse_action():
            if action.action_type == DesktopActionType.MOUSE_MOVE:
                pyautogui.moveTo(x, y)
            elif action.action_type == DesktopActionType.MOUSE_CLICK:
                button = action.payload.get("button", "left")
                if x is not None and y is not None:
                    pyautogui.click(x, y, button=button)
                else:
                    pyautogui.click(button=button)
            elif action.action_type == DesktopActionType.MOUSE_DOUBLE_CLICK:
                if x is not None and y is not None:
                    pyautogui.doubleClick(x, y)
                else:
                    pyautogui.doubleClick()
            elif action.action_type == DesktopActionType.MOUSE_SCROLL:
                amount = action.payload.get("amount", 0)
                pyautogui.scroll(amount)
                
        await asyncio.to_thread(_mouse_action)
        return True

class WindowsKeyboardController:
    async def execute(self, action: DesktopAction) -> Any:
        def _keyboard_action():
            time.sleep(0.5)
            # Clear any stuck modifier keys
            for mod in ['ctrl', 'shift', 'alt', 'win']:
                pyautogui.keyUp(mod)
                
            if action.action_type == DesktopActionType.KEYBOARD_TYPE:
                text = action.payload.get("text", "")
                pyautogui.write(text, interval=0.05)
            elif action.action_type == DesktopActionType.KEYBOARD_SHORTCUT:
                keys = action.payload.get("keys", [])
                pyautogui.hotkey(*keys)
                if "enter" in keys:
                    time.sleep(2.5) # Wait for search results or page to load
                
        await asyncio.to_thread(_keyboard_action)
        return True

class WindowsClipboardManager:
    async def execute(self, action: DesktopAction) -> Any:
        def _clipboard():
            if action.action_type == DesktopActionType.CLIPBOARD_READ:
                return pyperclip.paste()
            elif action.action_type == DesktopActionType.CLIPBOARD_WRITE:
                text = action.payload.get("text", "")
                pyperclip.copy(text)
                return True
                
        return await asyncio.to_thread(_clipboard)

class WindowsScreenshotManager:
    async def execute(self, action: DesktopAction) -> Any:
        def _screenshot():
            path = action.payload.get("path", "desktop_screenshot.png")
            pyautogui.screenshot(path)
            return True
        return await asyncio.to_thread(_screenshot)

class WindowsFilesystemManager:
    async def execute(self, action: DesktopAction) -> Any:
        path = action.payload.get("path")
        if not path:
            raise ValueError(f"Path is required for {action.action_type}")
            
        def _fs_action():
            if action.action_type == DesktopActionType.FS_CREATE_DIRECTORY:
                os.makedirs(path, exist_ok=True)
                return True
            elif action.action_type == DesktopActionType.FS_CREATE_FILE:
                with open(path, 'a') as f:
                    pass
                return True
            elif action.action_type == DesktopActionType.FS_WRITE:
                text = action.payload.get("text", "")
                mode = action.payload.get("mode", "w")
                with open(path, mode, encoding='utf-8') as f:
                    f.write(text)
                return True
            elif action.action_type == DesktopActionType.FS_READ:
                with open(path, 'r', encoding='utf-8') as f:
                    return f.read()
            elif action.action_type == DesktopActionType.FS_COPY:
                dest = action.payload.get("destination")
                if not dest:
                    raise ValueError("Destination is required for FS_COPY")
                if os.path.isdir(path):
                    shutil.copytree(path, dest)
                else:
                    shutil.copy2(path, dest)
                return True
            elif action.action_type == DesktopActionType.FS_MOVE:
                dest = action.payload.get("destination")
                if not dest:
                    raise ValueError("Destination is required for FS_MOVE")
                shutil.move(path, dest)
                return True
            elif action.action_type == DesktopActionType.FS_RENAME:
                new_name = action.payload.get("new_name") or action.payload.get("destination")
                if not new_name:
                    raise ValueError("new_name/destination is required for FS_RENAME")
                os.rename(path, new_name)
                return True
            elif action.action_type == DesktopActionType.FS_DELETE:
                if os.path.isdir(path):
                    shutil.rmtree(path)
                else:
                    os.remove(path)
                return True
            elif action.action_type == DesktopActionType.FS_LIST:
                return os.listdir(path)
            
            return False
            
        return await asyncio.to_thread(_fs_action)

class WindowsProcessManager:
    async def execute(self, action: DesktopAction) -> Any:
        def _process_action():
            pass # Use process specific enums if needed
            return True
        return await asyncio.to_thread(_process_action)

class WindowsNotificationManager:
    async def execute(self, action: DesktopAction) -> Any:
        # Simple print for now, full toast notification requires more win32 wiring
        app_logger.info(f"System Notification: {action.payload}")
        return True

class WindowsMonitorManager:
    async def execute(self, action: DesktopAction) -> Any:
        return True

class WindowsShortcutManager:
    async def execute(self, action: DesktopAction) -> Any:
        return True

from backend.desktop.controllers.registry import AppActionRouter

class WindowsIntentManager:
    def __init__(self):
        self.router = AppActionRouter()
        
    async def execute(self, action: DesktopAction) -> Any:
        if action.action_type == DesktopActionType.APP_INTENT_EXECUTE:
            app_name = action.payload.get("app")
            intent = action.payload.get("intent")
            entity = action.payload.get("entity")
            if not app_name or not intent:
                raise ValueError("app and intent are required for APP_INTENT_EXECUTE")
                
            def _execute_intent():
                return self.router.execute(app_name, intent, entity)
                
            success = await asyncio.to_thread(_execute_intent)
            if not success:
                app_logger.error(f"Intent {intent} for {app_name} failed to execute.")
            return success
        return False
