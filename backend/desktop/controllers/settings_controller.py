import time
import os
import subprocess
import traceback
from typing import Optional
from backend.desktop.controllers.base_controller import AppController
from backend.core.logger import app_logger

try:
    import psutil
except ImportError:
    psutil = None

class SettingsController(AppController):
    """Dedicated controller for Windows Settings.
    Handles instant deep navigation across all Windows Settings pages and UWP controls.
    """
    
    TAB_MAP = {
        "update": "ms-settings:windowsupdate",
        "updates": "ms-settings:windowsupdate",
        "windows update": "ms-settings:windowsupdate",
        "updates and security": "ms-settings:windowsupdate",
        "update and security": "ms-settings:windowsupdate",
        "windows updates": "ms-settings:windowsupdate",
        "check for updates": "ms-settings:windowsupdate",
        "security": "ms-settings:windowsupdate",
        "privacy": "ms-settings:privacy",
        "privacy & security": "ms-settings:privacy",
        "display": "ms-settings:display",
        "screen": "ms-settings:display",
        "sound": "ms-settings:sound",
        "volume": "ms-settings:sound",
        "notifications": "ms-settings:notifications",
        "power": "ms-settings:powersleep",
        "battery": "ms-settings:powersleep",
        "storage": "ms-settings:storagesense",
        "bluetooth": "ms-settings:bluetooth",
        "devices": "ms-settings:bluetooth",
        "bluetooth & devices": "ms-settings:bluetooth",
        "network": "ms-settings:network",
        "internet": "ms-settings:network",
        "wifi": "ms-settings:network-wifi",
        "wi-fi": "ms-settings:network-wifi",
        "personalization": "ms-settings:personalization",
        "background": "ms-settings:personalization-background",
        "themes": "ms-settings:themes",
        "colors": "ms-settings:colors",
        "apps": "ms-settings:appsfeatures",
        "installed apps": "ms-settings:appsfeatures",
        "default apps": "ms-settings:defaultapps",
        "accounts": "ms-settings:yourinfo",
        "time": "ms-settings:dateandtime",
        "date": "ms-settings:dateandtime",
        "language": "ms-settings:regionlanguage",
        "gaming": "ms-settings:gaming-gamebar",
        "accessibility": "ms-settings:easeofaccess-display",
    }

    def __init__(self):
        self.title_re = ".*Settings.*"

    def is_open(self) -> bool:
        if psutil:
            try:
                for p in psutil.process_iter(['name']):
                    name = p.info.get('name') or ''
                    if 'systemsettings' in name.lower():
                        return True
            except Exception:
                pass
        return False

    def launch(self, target_uri: str = "ms-settings:"):
        try:
            os.startfile(target_uri)
        except Exception as e:
            app_logger.error(f"Failed to launch Settings ({target_uri}): {e}")

    def wait_ready(self, timeout: int = 5) -> bool:
        for _ in range(timeout * 2):
            if self.is_open():
                return True
            time.sleep(0.5)
        # Even if process check is delayed, UWP startfile handles launch asynchronously
        return True

    def _resolve_uri(self, query: str) -> str:
        q = query.lower().strip()
        for key, uri in self.TAB_MAP.items():
            if key in q or q in key:
                return uri
        return "ms-settings:"

    def execute(self, intent: str, entity: Optional[str]) -> bool:
        try:
            app_logger.info(f"SettingsController.execute: intent='{intent}', entity='{entity}'")
            
            if intent in ["open_app", "launch"]:
                target_uri = "ms-settings:"
                if entity:
                    target_uri = self._resolve_uri(entity)
                self.launch(target_uri)
                return True
                
            elif intent in ["navigate_to_tab", "navigate", "open_tab", "go_to_tab"]:
                target_uri = self._resolve_uri(entity or "")
                app_logger.info(f"Navigating to Settings tab '{entity}' via URI: {target_uri}")
                self.launch(target_uri)
                time.sleep(1.5)
                
                # If they navigated to update, trigger update check if requested
                if "update" in (entity or "").lower() or "check" in (entity or "").lower():
                    try:
                        import pyautogui
                        time.sleep(1.0)
                        pyautogui.press('enter')
                    except Exception:
                        pass
                return True

            elif intent in ["check_updates", "check_for_updates"] or (entity and "update" in entity.lower()):
                app_logger.info("SettingsController: Navigating to Windows Update directly")
                self.launch("ms-settings:windowsupdate")
                time.sleep(2.0)
                try:
                    import pyautogui
                    pyautogui.press('enter')
                except Exception:
                    pass
                return True

            elif intent == "search" and entity:
                self.launch("ms-settings:")
                time.sleep(1.5)
                try:
                    import pyautogui
                    pyautogui.hotkey('ctrl', 'e')
                    time.sleep(0.3)
                    pyautogui.write(entity, interval=0.04)
                    pyautogui.press('enter')
                    return True
                except Exception as se:
                    app_logger.error(f"Settings search failed: {se}")
                    return False

            elif entity:
                # Default fallback: try to resolve entity as a tab name
                target_uri = self._resolve_uri(entity)
                self.launch(target_uri)
                return True

            return False
            
        except Exception as e:
            app_logger.error(f"SettingsController execute failed: {e}\n{traceback.format_exc()}")
            return False
