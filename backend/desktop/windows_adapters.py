import asyncio
import os
import shutil
import psutil
import time
from typing import Any, Optional, Dict, List
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

def _ensure_desktop():
    try:
        import ctypes
        user32 = ctypes.windll.user32
        h_default = user32.OpenDesktopW("Default", 0, False, 0x01FF)
        if h_default:
            user32.SetThreadDesktop(h_default)
    except Exception:
        pass

class WindowsApplicationManager:
    async def execute(self, action: DesktopAction) -> Any:
        app_name_or_path = action.payload.get("path") or action.payload.get("name")
        if action.action_type == DesktopActionType.APP_LAUNCH:
            if not app_name_or_path:
                raise ValueError("App path or name required for APP_LAUNCH")
            
            def _launch():
                _ensure_desktop()
                # Map common names to Windows executables
                app_map = {
                    "calculator": "calculator:",
                    "notepad": "notepad.exe",
                    "paint": "mspaint.exe",
                    "wordpad": "write.exe",
                    "explorer": "explorer.exe",
                    "browser": "msedge.exe",
                    "spotify": "spotify:",
                    "settings": "ms-settings:",
                    "task manager": "taskmgr.exe",
                    "recycle bin": "shell:RecycleBinFolder",
                    "whatsapp": "whatsapp:",
                    "brave": "brave.exe",
                    "chrome": "chrome.exe",
                    "edge": "msedge.exe",
                    "firefox": "firefox.exe"
                }
                exe_name = app_name_or_path
                for key, mapped_name in app_map.items():
                    if key in app_name_or_path.lower():
                        exe_name = mapped_name
                        break
                
                app_logger.info(f"WindowsApplicationManager: app_name_or_path={app_name_or_path}, mapped to exe_name={exe_name}")

                # Handle URL navigation with browser
                url = action.payload.get("url")
                if not url and action.payload.get("entity") and "http" in str(action.payload.get("entity")):
                    url = action.payload.get("entity")

                is_background = bool(action.payload.get("background") or action.payload.get("keep_in_background"))
                additional_urls = action.payload.get("additional_urls", [])
                file_path_payload = action.payload.get("file_path") or action.payload.get("path")
                upload_to_service = bool(action.payload.get("upload_to_service"))

                # If a local file is provided, copy path to clipboard for instant upload / paste in browser
                if file_path_payload and os.path.exists(file_path_payload):
                    try:
                        import pyperclip
                        pyperclip.copy(file_path_payload)
                        app_logger.info(f"Copied file path to clipboard for instant upload: {file_path_payload}")
                    except Exception:
                        pass

                current_fg = None
                try:
                    import win32gui
                    current_fg = win32gui.GetForegroundWindow()
                except Exception:
                    pass

                def _restore_fg_if_background():
                    if is_background and current_fg:
                        time.sleep(0.4)
                        try:
                            import win32gui
                            win32gui.SetForegroundWindow(current_fg)
                        except Exception:
                            pass

                def _automate_docs_upload(fpath: str, is_bg: bool, orig_fg: Optional[int]):
                    """Automates file upload picker sequence in Google Docs."""
                    try:
                        import win32gui, win32con, pyautogui, pyperclip
                        time.sleep(2.5)
                        c_hwnd = None
                        def find_docs_cb(h, _):
                            nonlocal c_hwnd
                            if win32gui.IsWindowVisible(h):
                                t = win32gui.GetWindowText(h).lower()
                                if "google docs" in t and "chrome" in t:
                                    c_hwnd = h
                        win32gui.EnumWindows(find_docs_cb, None)
                        if c_hwnd:
                            rect = win32gui.GetWindowRect(c_hwnd)
                            wx, wy = rect[0], rect[1]
                            # Click folder icon (Open file picker)
                            pyautogui.click(wx + 820, wy + 505)
                            time.sleep(1.5)
                            # Click Upload tab
                            pyautogui.click(wx + 640, wy + 315)
                            time.sleep(1.2)
                            # Click Browse button
                            pyautogui.click(wx + 516, wy + 607)
                            time.sleep(1.0)
                            # Paste file path and submit
                            pyperclip.copy(fpath)
                            pyautogui.hotkey('ctrl', 'v')
                            time.sleep(0.3)
                            pyautogui.press('enter')
                            time.sleep(2.5)
                            if is_bg and orig_fg:
                                try:
                                    win32gui.SetForegroundWindow(orig_fg)
                                except Exception:
                                    pass
                    except Exception as ex:
                        app_logger.warning(f"Google Docs upload automation notice: {ex}")

                def _focus_window(title_substr: str):
                    if is_background:
                        _restore_fg_if_background()
                        return
                    try:
                        _ensure_desktop()
                        import win32gui, win32con
                        time.sleep(1.5)
                        def cb(hwnd, _):
                            if win32gui.IsWindowVisible(hwnd):
                                t = win32gui.GetWindowText(hwnd)
                                if title_substr.lower() in t.lower():
                                    win32gui.ShowWindow(hwnd, win32con.SW_RESTORE)
                                    try:
                                        win32gui.SetForegroundWindow(hwnd)
                                    except Exception:
                                        pass
                        win32gui.EnumWindows(cb, None)
                    except Exception as e:
                        app_logger.warning(f"Failed to focus window {title_substr}: {e}")

                # Helper: Candidate browser paths on Windows
                def _find_browser_exe(browser_type: str) -> Optional[str]:
                    b_type = browser_type.lower()
                    candidates = []
                    if "chrome" in b_type:
                        candidates = [
                            r"C:\Program Files\Google\Chrome\Application\chrome.exe",
                            r"C:\Program Files (x86)\Google\Chrome\Application\chrome.exe",
                            os.path.expandvars(r"%LOCALAPPDATA%\Google\Chrome\Application\chrome.exe"),
                            os.path.expandvars(r"%PROGRAMFILES%\Google\Chrome\Application\chrome.exe"),
                            os.path.expandvars(r"%PROGRAMFILES(X86)%\Google\Chrome\Application\chrome.exe"),
                        ]
                    elif "brave" in b_type:
                        candidates = [
                            r"C:\Program Files\BraveSoftware\Brave-Browser\Application\brave.exe",
                            r"C:\Program Files (x86)\BraveSoftware\Brave-Browser\Application\brave.exe",
                            os.path.expandvars(r"%LOCALAPPDATA%\BraveSoftware\Brave-Browser\Application\brave.exe"),
                        ]
                    elif "edge" in b_type:
                        candidates = [
                            r"C:\Program Files (x86)\Microsoft\Edge\Application\msedge.exe",
                            r"C:\Program Files\Microsoft\Edge\Application\msedge.exe",
                            os.path.expandvars(r"%LOCALAPPDATA%\Microsoft\Edge\Application\msedge.exe"),
                        ]
                    else:
                        # Fallback order for generic "browser"
                        candidates = [
                            r"C:\Program Files\Google\Chrome\Application\chrome.exe",
                            r"C:\Program Files\BraveSoftware\Brave-Browser\Application\brave.exe",
                            r"C:\Program Files (x86)\Microsoft\Edge\Application\msedge.exe",
                            r"C:\Program Files (x86)\Google\Chrome\Application\chrome.exe",
                            os.path.expandvars(r"%LOCALAPPDATA%\Google\Chrome\Application\chrome.exe"),
                        ]
                    for path in candidates:
                        if path and os.path.exists(path):
                            return path
                    return None

                target_browser_kw = "chrome" if "chrome" in app_name_or_path.lower() else "brave" if "brave" in app_name_or_path.lower() else "edge" if "edge" in app_name_or_path.lower() else "browser"

                if url:
                    # In background mode (e.g. user working in Antigravity or gaming),
                    # NEVER steal focus or send simulated keystrokes to the foreground window.
                    # Spawning the browser executable with the URL instructs Chrome/Brave/Edge's native IPC
                    # to open the tab silently in the background while keeping Antigravity undisturbed.
                    if is_background:
                        browser_exe = _find_browser_exe(target_browser_kw)
                        if browser_exe:
                            import subprocess
                            app_logger.info(f"Background launch: {browser_exe} -> {url}")
                            cflags = 0x08000000  # CREATE_NO_WINDOW
                            startupinfo = subprocess.STARTUPINFO()
                            startupinfo.dwFlags |= subprocess.STARTF_USESHOWWINDOW
                            startupinfo.wShowWindow = 7  # SW_SHOWMINNOACTIVE
                            subprocess.Popen([browser_exe, url], creationflags=cflags, startupinfo=startupinfo)
                            _restore_fg_if_background()
                            if upload_to_service and file_path_payload and "docs.google.com" in str(url) and "/document/d/" not in str(url):
                                import threading
                                threading.Thread(target=_automate_docs_upload, args=(file_path_payload, is_background, current_fg), daemon=True).start()
                            return

                    # 1. If browser window is already open and user is NOT in background mode,
                    # focus it and open a new tab directly
                    try:
                        _ensure_desktop()
                        import win32gui, win32con, pyautogui, pyperclip
                        matched_hwnd = None
                        def find_cb(h, _):
                            nonlocal matched_hwnd
                            if win32gui.IsWindowVisible(h):
                                title = win32gui.GetWindowText(h).lower()
                                if target_browser_kw != "browser":
                                    if target_browser_kw in title:
                                        matched_hwnd = h
                                elif any(k in title for k in ["chrome", "brave", "edge"]):
                                    matched_hwnd = h
                        win32gui.EnumWindows(find_cb, None)
                        if matched_hwnd:
                            app_logger.info(f"Existing browser window found ({hex(matched_hwnd)}). Opening new tab with {url}")
                            win32gui.ShowWindow(matched_hwnd, win32con.SW_RESTORE)
                            win32gui.SetForegroundWindow(matched_hwnd)
                            time.sleep(0.3)
                            pyautogui.hotkey('ctrl', 't')
                            time.sleep(0.3)
                            pyperclip.copy(url)
                            pyautogui.hotkey('ctrl', 'v')
                            time.sleep(0.1)
                            pyautogui.press('enter')

                            # Open any additional URLs in extra tabs
                            for a_url in additional_urls:
                                time.sleep(0.3)
                                pyautogui.hotkey('ctrl', 't')
                                time.sleep(0.2)
                                pyperclip.copy(a_url)
                                pyautogui.hotkey('ctrl', 'v')
                                time.sleep(0.1)
                                pyautogui.press('enter')
                            return
                    except Exception as e:
                        app_logger.warning(f"Active browser tab injection failed: {e}")

                    # 2. Cold launch with URL
                    browser_exe = _find_browser_exe(target_browser_kw)
                    if browser_exe:
                        import subprocess
                        app_logger.info(f"Launching {browser_exe} directly with URL: {url} (background={is_background})")
                        cflags = 0x08000000  # CREATE_NO_WINDOW
                        launch_cmd = [browser_exe, url]
                        if additional_urls and isinstance(additional_urls, list):
                            launch_cmd.extend(additional_urls)

                        startupinfo = None
                        if is_background:
                            startupinfo = subprocess.STARTUPINFO()
                            startupinfo.dwFlags |= subprocess.STARTF_USESHOWWINDOW
                            startupinfo.wShowWindow = 7  # SW_SHOWMINNOACTIVE

                        subprocess.Popen(launch_cmd, creationflags=cflags, startupinfo=startupinfo)
                        if is_background:
                            _restore_fg_if_background()
                        else:
                            _focus_window(target_browser_kw)
                        return

                    try:
                        app_logger.info(f"Opening URL via default browser: {url}")
                        os.startfile(url)
                        if is_background:
                            _restore_fg_if_background()
                        else:
                            _focus_window(app_name_or_path or "browser")
                        return
                    except Exception as e:
                        app_logger.warning(f"os.startfile({url}) failed: {e}")

                # Standard app launch (no URL)
                # First check if this is a known browser to launch directly
                if target_browser_kw in ["chrome", "brave", "edge"]:
                    browser_exe = _find_browser_exe(target_browser_kw)
                    if browser_exe:
                        import subprocess
                        app_logger.info(f"Launching browser directly: {browser_exe} (background={is_background})")
                        cflags = 0x08000000  # CREATE_NO_WINDOW
                        startupinfo = None
                        if is_background:
                            startupinfo = subprocess.STARTUPINFO()
                            startupinfo.dwFlags |= subprocess.STARTF_USESHOWWINDOW
                            startupinfo.wShowWindow = 7  # SW_SHOWMINNOACTIVE
                        subprocess.Popen([browser_exe], creationflags=cflags, startupinfo=startupinfo)
                        if is_background:
                            _restore_fg_if_background()
                        else:
                            _focus_window(target_browser_kw)
                        return

                try:
                    app_logger.info(f"Trying os.startfile({exe_name}) (background={is_background})")
                    if is_background:
                        import win32api, win32con
                        win32api.ShellExecute(0, "open", exe_name, None, None, win32con.SW_SHOWMINNOACTIVE)
                        _restore_fg_if_background()
                    else:
                        os.startfile(exe_name)
                        app_logger.info("os.startfile succeeded")
                        _focus_window(app_name_or_path)
                except Exception as e:
                    app_logger.warning(f"os.startfile failed: {e}. Falling back to pywinauto.")
                    # fallback to pywinauto if it's an exe that needs hooking
                    pywinauto.Application(backend="uia").start(exe_name)
                    _focus_window(app_name_or_path)
            
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
            if success and self.router.last_output:
                action.payload["output"] = self.router.last_output
            if not success:
                app_logger.error(f"Intent {intent} for {app_name} failed to execute.")
            return success
        return False
