import time
import subprocess
import os
import pyautogui
from typing import Optional
from backend.desktop.controllers.base_controller import AppController
from backend.core.logger import app_logger

class SpotifyController(AppController):
    """Dedicated controller for Spotify.
    Spotify is an Electron/CEF app, so standard UIA accessibility trees are heavily nested or hidden.
    This controller uses a robust keyboard macro fallback for reliable execution.
    """
    
    def is_open(self) -> bool:
        # Check if Spotify is in the tasklist
        try:
            output = subprocess.check_output("tasklist /FI \"IMAGENAME eq spotify.exe\"", shell=True).decode()
            return "spotify.exe" in output.lower()
        except Exception:
            return False

    def launch(self):
        try:
            os.startfile("spotify:")
        except Exception as e:
            app_logger.error(f"Failed to launch Spotify: {e}")

    def wait_ready(self, timeout: int = 10) -> bool:
        for _ in range(timeout):
            if self.is_open():
                # Give it an extra second to draw the window
                time.sleep(1)
                return True
            time.sleep(1)
        return False

    def execute(self, intent: str, entity: Optional[str]) -> bool:
        try:
            if intent == "open_app":
                os.startfile("spotify:")
                return True
                
            elif intent == "play_media" and entity:
                # 1. Bring Spotify to front
                os.startfile("spotify:")
                time.sleep(1) # Wait for focus
                
                # 2. Focus Search (Ctrl+L or Ctrl+K)
                pyautogui.hotkey('ctrl', 'l')
                time.sleep(0.4)
                
                # 3. Type search entity
                pyautogui.write(entity, interval=0.04)
                time.sleep(0.4)
                
                # 4. Press Enter to search
                pyautogui.press('enter')
                
                # 5. Wait for search results
                time.sleep(2.0)
                
                # 6. Tab to top result and play
                pyautogui.press('tab')
                time.sleep(0.1)
                pyautogui.press('tab')
                time.sleep(0.1)
                pyautogui.press('enter')
                return True
                
            elif intent in ["pause", "pause_media", "resume", "play", "toggle_play"]:
                # Space bar or Play/Pause media key
                pyautogui.press('playpause')
                return True
                
            elif intent in ["next", "next_track", "skip"]:
                pyautogui.press('nexttrack')
                return True
                
            elif intent in ["prev", "previous", "previous_track"]:
                pyautogui.press('prevtrack')
                return True

        except Exception as e:
            app_logger.error(f"SpotifyController execute failed: {e}")
            return False
            
        return False
