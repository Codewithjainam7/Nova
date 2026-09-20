import json
import os
import subprocess
from typing import Dict, Any, Optional
from backend.core.logger import app_logger

class DeviceManager:
    """Manages connections and commands to external devices (like Android phones via ADB)."""
    
    def __init__(self):
        self.connected_devices = []
        self.devices_file = os.path.join(os.path.dirname(__file__), "known_devices.json")
        self._load_devices()
        
        # Use absolute path to the downloaded platform-tools
        self.adb_path = os.path.join(os.path.dirname(os.path.dirname(os.path.dirname(__file__))), "platform-tools", "adb.exe")
        self._check_adb()

    def _load_devices(self):
        if os.path.exists(self.devices_file):
            try:
                with open(self.devices_file, "r") as f:
                    self.connected_devices = json.load(f)
            except Exception:
                self.connected_devices = []

    def _save_devices(self):
        try:
            with open(self.devices_file, "w") as f:
                json.dump(self.connected_devices, f)
        except Exception:
            pass

    def _check_adb(self):
        try:
            result = subprocess.run([self.adb_path, "version"], capture_output=True, text=True)
            if result.returncode == 0:
                app_logger.info("ADB found on system.")
            else:
                app_logger.warning("ADB command returned non-zero. ADB might not be installed.")
        except Exception as e:
            app_logger.warning(f"ADB not found in PATH: {e}. Please install Android platform-tools.")

    def pair(self, ip_port: str, code: str) -> bool:
        """Pair with an Android device over Wi-Fi using Android 11+ pairing code."""
        try:
            app_logger.info(f"Attempting to pair with device at {ip_port} using code {code}")
            result = subprocess.run([self.adb_path, "pair", ip_port, code], capture_output=True, text=True)
            if "successfully paired to" in result.stdout.lower():
                app_logger.info(f"Successfully paired to {ip_port}")
                return True
            else:
                app_logger.error(f"Failed to pair to {ip_port}: {result.stdout}")
                return False
        except Exception as e:
            app_logger.error(f"ADB pair exception: {e}")
            return False

    def connect(self, ip_port: str) -> bool:
        """Connect to an Android device over Wi-Fi."""
        try:
            app_logger.info(f"Attempting to connect to device at {ip_port}")
            result = subprocess.run([self.adb_path, "connect", ip_port], capture_output=True, text=True)
            if "connected to" in result.stdout.lower() or "already connected" in result.stdout.lower():
                app_logger.info(f"Successfully connected to {ip_port}")
                if ip_port not in self.connected_devices:
                    self.connected_devices.append(ip_port)
                    self._save_devices()
                return True
            else:
                app_logger.error(f"Failed to connect to {ip_port}: {result.stdout}")
                return False
        except Exception as e:
            app_logger.error(f"ADB connect exception: {e}")
            return False

    def get_connected_devices(self) -> list:
        try:
            result = subprocess.run([self.adb_path, "devices"], capture_output=True, text=True)
            devices = []
            for line in result.stdout.splitlines()[1:]:
                if "device" in line and "offline" not in line and "unauthorized" not in line:
                    parts = line.split('\t')
                    if len(parts) > 0:
                        devices.append(parts[0].strip())
            return devices
        except Exception:
            return self.connected_devices

    def get_battery_level(self, device_ip: Optional[str] = None) -> str:
        """Gets the battery level of the connected device."""
        active_devices = self.get_connected_devices()
        
        if not active_devices and not self.connected_devices:
            return "No device connected. Please pair or connect your phone first."
            
        target = device_ip
        if not target:
            if active_devices:
                target = active_devices[0]
            else:
                target = self.connected_devices[0]
        
        # Ensure it's connected just in case the ADB daemon dropped it, only if it's an IP
        if ":" in target:
            self.connect(target)
        
        try:
            result = subprocess.run(
                [self.adb_path, "-s", target, "shell", "dumpsys", "battery"], 
                capture_output=True, text=True
            )
            for line in result.stdout.split('\n'):
                if "level:" in line:
                    level = line.split(":")[1].strip()
                    return f"{level}%"
            return "Could not read battery level."
        except Exception as e:
            app_logger.error(f"Failed to get battery: {e}")
            return f"Error reading battery: {e}"

    def unlock_device(self, target: str):
        """Wakes up the screen and unlocks the device if a PIN is configured."""
        try:
            import time
            from dotenv import load_dotenv
            load_dotenv()
            
            ADB_TIMEOUT = 15  # Wireless ADB can be slow
            
            # Step 1: Wake up screen using POWER button (keyevent 26)
            # Use grep on device side to avoid transferring entire dumpsys output
            result = subprocess.run(
                [self.adb_path, "-s", target, "shell", "dumpsys power | grep mWakefulness"],
                capture_output=True, text=True, timeout=ADB_TIMEOUT
            )
            if "mWakefulness=Awake" not in result.stdout:
                app_logger.info(f"[{target}] Waking up screen with POWER button.")
                subprocess.run([self.adb_path, "-s", target, "shell", "input", "keyevent", "26"], timeout=ADB_TIMEOUT)
                time.sleep(2.0)
            else:
                app_logger.info(f"[{target}] Screen already awake.")
                
            # Step 2: Check if locked and unlock with PIN
            result = subprocess.run(
                [self.adb_path, "-s", target, "shell", "dumpsys window | grep -E 'mShowingLockscreen|mDreamingLockscreen|isStatusBarKeyguard'"],
                capture_output=True, text=True, timeout=ADB_TIMEOUT
            )
            lock_info = result.stdout
            if "mShowingLockscreen=true" in lock_info or "mDreamingLockscreen=true" in lock_info or "isStatusBarKeyguard=true" in lock_info:
                app_logger.info(f"[{target}] Unlocking device.")
                # Swipe up to show PIN pad
                subprocess.run([self.adb_path, "-s", target, "shell", "input", "swipe", "500", "1500", "500", "500"], timeout=ADB_TIMEOUT)
                time.sleep(1.0)
                
                pin = os.getenv("ANDROID_PIN")
                if pin:
                    subprocess.run([self.adb_path, "-s", target, "shell", "input", "text", pin], timeout=ADB_TIMEOUT)
                    time.sleep(0.5)
                    subprocess.run([self.adb_path, "-s", target, "shell", "input", "keyevent", "66"], timeout=ADB_TIMEOUT)
                    time.sleep(1.5)
            else:
                app_logger.info(f"[{target}] Device not locked.")
            
            # Step 3: Go to home screen to ensure a clean state
            app_logger.info(f"[{target}] Returning to home screen.")
            subprocess.run([self.adb_path, "-s", target, "shell", "input", "keyevent", "3"], timeout=ADB_TIMEOUT)
            time.sleep(0.5)
        except Exception as e:
            app_logger.error(f"Failed to unlock device: {e}")

    def execute_action(self, intent: str, entity: str, **kwargs) -> str:
        """Executes a semantic action on the primary connected device."""
        active_devices = self.get_connected_devices()
        
        if not active_devices and not self.connected_devices:
            return "Cannot execute action. No phone is currently connected."
            
        target = active_devices[0] if active_devices else self.connected_devices[0]
        
        # Ensure connected
        if ":" in target:
            success = self.connect(target)
            if not success:
                return "Cannot execute action. Failed to connect to device."
            
        if intent == "get_battery":
            level = self.get_battery_level(target)
            return f"Your phone battery is currently at {level}."
            
        if intent == "open_app":
            if not entity:
                return "Cannot open app. No application or file name specified."
                
            # Redirect to play_media if a search/play query is specified
            media_query = kwargs.get("entity_2") or kwargs.get("query")
            if media_query and entity.lower() in ("youtube", "spotify"):
                return self.execute_action("play_media", media_query, app=entity, **kwargs)

            # Check if entity is actually a file name
            import os
            _, ext = os.path.splitext(entity)
            if ext and ext.lower() in (".png", ".jpg", ".jpeg", ".pdf", ".txt", ".gif", ".mp4", ".mp3", ".doc", ".docx", ".xls", ".xlsx"):
                try:
                    self.unlock_device(target)
                    import mimetypes
                    mime_type, _ = mimetypes.guess_type(entity)
                    if not mime_type:
                        if ext.lower() in (".png", ".jpg", ".jpeg", ".gif"):
                            mime_type = "image/*"
                        elif ext.lower() == ".pdf":
                            mime_type = "application/pdf"
                        elif ext.lower() == ".txt":
                            mime_type = "text/plain"
                        else:
                            mime_type = "*/*"
                            
                    file_uri = f"file:///sdcard/Download/{entity}"
                    cmd = [self.adb_path, "-s", target, "shell", "am", "start", "-a", "android.intent.action.VIEW", "-d", file_uri, "-t", mime_type]
                    app_logger.info(f"[{target}] Opening file {entity} with command: {' '.join(cmd)}")
                    result = subprocess.run(cmd, capture_output=True, text=True, timeout=15)
                    if result.returncode == 0:
                        return f"Successfully opened {entity} on your phone."
                    else:
                        return f"Failed to open file {entity} on phone: {result.stderr or result.stdout}"
                except Exception as e:
                    return f"Failed to open file {entity}: {e}"

            app_package_map = {
                "spotify": "com.spotify.music",
                "youtube": "com.google.android.youtube",
                "chrome": "com.android.chrome",
                "maps": "com.google.android.apps.maps",
                "calculator": "com.google.android.calculator",
                "files": "com.google.android.apps.nbu.files",
                "google files": "com.google.android.apps.nbu.files",
                "downloads": "com.android.providers.downloads.ui"
            }
            package = app_package_map.get(entity.lower(), entity.lower())
            try:
                self.unlock_device(target)
                result = subprocess.run(
                    [self.adb_path, "-s", target, "shell", "monkey", "-p", package, "-c", "android.intent.category.LAUNCHER", "1"],
                    capture_output=True, text=True, timeout=15
                )
                if "monkey aborted" in result.stdout.lower() or result.returncode != 0:
                    return f"Failed to open {entity} on phone: app package '{package}' is not installed or not launchable."
                return f"Successfully opened {entity} on your phone."
            except Exception as e:
                return f"Failed to open {entity} on phone: {e}"
                
        if intent == "play_media":
            try:
                # Use Android's built-in media search intent to play songs
                query = entity.lower()
                target_app = kwargs.get("app", "").lower()
                package = None
                
                if "youtube" in target_app or "youtube" in query:
                    package = "com.google.android.youtube"
                    query = query.replace("on youtube", "").replace("in youtube", "").replace("youtube", "").strip()
                elif "spotify" in target_app or "spotify" in query:
                    package = "com.spotify.music"
                    query = query.replace("on spotify", "").replace("in spotify", "").replace("spotify", "").strip()
                else:
                    # Default to Spotify for generic play commands
                    package = "com.spotify.music"
                
                if not query:
                    query = entity
                    
                self.unlock_device(target)
                    
                cmd = [self.adb_path, "-s", target, "shell", "am", "start", "-a", "android.media.action.MEDIA_PLAY_FROM_SEARCH"]
                if package:
                    cmd.extend(["-p", package])
                cmd.extend(["-e", "query", query])
                
                subprocess.run(cmd, capture_output=True, text=True)
                
                # If YouTube, we need to inject a DPAD_DOWN and ENTER to actually click the first video
                if package == "com.google.android.youtube":
                    import time
                    time.sleep(3.0)
                    subprocess.run([self.adb_path, "-s", target, "shell", "input", "keyevent", "20"]) # DPAD DOWN
                    time.sleep(0.5)
                    subprocess.run([self.adb_path, "-s", target, "shell", "input", "keyevent", "20"]) # DPAD DOWN
                    time.sleep(0.5)
                    subprocess.run([self.adb_path, "-s", target, "shell", "input", "keyevent", "66"]) # ENTER
                elif package == "com.spotify.music":
                    import time
                    time.sleep(3.0)
                    # For Spotify, tapping the first result (Y=460) is much more reliable than DPAD since the keyboard traps it
                    subprocess.run([self.adb_path, "-s", target, "shell", "input", "tap", "500", "460"])
                
                return f"Playing {query} on your phone."
            except Exception as e:
                return f"Failed to play media: {e}"
        if intent == "search":
            try:
                self.unlock_device(target)
                if "on youtube" in entity.lower():
                    query = entity.lower().replace("on youtube", "").strip()
                    if not query:
                        query = entity
                    subprocess.run([
                        self.adb_path, "-s", target, "shell", "am", "start", 
                        "-a", "android.intent.action.SEARCH", 
                        "-p", "com.google.android.youtube", 
                        "-e", "query", query
                    ])
                    return f"Searching for {query} on YouTube."
                else:
                    subprocess.run([
                        self.adb_path, "-s", target, "shell", "am", "start", 
                        "-a", "android.intent.action.WEB_SEARCH", 
                        "-e", "query", entity
                    ])
                    return f"Searching for {entity} on your phone."
            except Exception as e:
                return f"Failed to search: {e}"

        if intent == "send_message":
            try:
                self.unlock_device(target)
                contact = entity
                message = kwargs.get("message", "")
                app = kwargs.get("app", "whatsapp").lower()
                
                app_logger.info(f"[{target}] Sending {app} message to '{contact}': {message}")
                
                import time
                if app == "telegram":
                    # Launch Telegram
                    subprocess.run([self.adb_path, "-s", target, "shell", "monkey", "-p", "org.telegram.messenger", "-c", "android.intent.category.LAUNCHER", "1"])
                    time.sleep(3.0)
                    
                    # Tap Search Icon (Top Right)
                    subprocess.run([self.adb_path, "-s", target, "shell", "input", "tap", "950", "150"])
                    time.sleep(1.0)
                    
                    # Type Contact Name
                    contact_safe = contact.replace(" ", "%s")
                    subprocess.run([self.adb_path, "-s", target, "shell", "input", "text", contact_safe])
                    time.sleep(2.0)
                    
                    # Close keyboard to see results
                    subprocess.run([self.adb_path, "-s", target, "shell", "input", "keyevent", "4"])
                    time.sleep(1.0)
                    
                    # Tap First Result (Below search header, around x=500, y=350)
                    subprocess.run([self.adb_path, "-s", target, "shell", "input", "tap", "500", "350"])
                    time.sleep(1.5)
                    
                    # Type Message
                    message_safe = message.replace(" ", "%s").replace("'", "\\'")
                    subprocess.run([self.adb_path, "-s", target, "shell", "input", "text", message_safe])
                    time.sleep(1.5)
                    
                    # Close keyboard
                    subprocess.run([self.adb_path, "-s", target, "shell", "input", "keyevent", "4"])
                    time.sleep(1.0)
                    
                    # Tap Send Button (Bottom Right, Telegram send button)
                    subprocess.run([self.adb_path, "-s", target, "shell", "input", "tap", "980", "2250"])
                    time.sleep(1.0)
                    
                    return f"Successfully sent Telegram message to {contact}."
                else:
                    # Default to WhatsApp
                    # Launch WhatsApp
                    subprocess.run([self.adb_path, "-s", target, "shell", "monkey", "-p", "com.whatsapp", "-c", "android.intent.category.LAUNCHER", "1"])
                    time.sleep(3.0)
                    
                    # Tap Search Icon
                    subprocess.run([self.adb_path, "-s", target, "shell", "input", "keyevent", "84"])
                    time.sleep(1.0)
                    
                    # Type Contact Name
                    contact_safe = contact.replace(" ", "%s")
                    subprocess.run([self.adb_path, "-s", target, "shell", "input", "text", contact_safe])
                    time.sleep(2.0)
                    
                    # Close keyboard to ensure first result is visible
                    subprocess.run([self.adb_path, "-s", target, "shell", "input", "keyevent", "4"])
                    time.sleep(1.0)
                    
                    # Tap First Result (Below search bar filters)
                    subprocess.run([self.adb_path, "-s", target, "shell", "input", "tap", "500", "600"])
                    time.sleep(1.5)
                    
                    # Type Message
                    message_safe = message.replace(" ", "%s").replace("'", "\\'")
                    subprocess.run([self.adb_path, "-s", target, "shell", "input", "text", message_safe])
                    time.sleep(1.5)
                    
                    # Close keyboard to ensure send button is at the bottom right
                    subprocess.run([self.adb_path, "-s", target, "shell", "input", "keyevent", "4"])
                    time.sleep(1.0)
                    
                    # Tap Send Button (Bottom Right, around 988 2319 on 2400h screens)
                    subprocess.run([self.adb_path, "-s", target, "shell", "input", "tap", "988", "2319"])
                    time.sleep(1.0)
                    
                    return f"Successfully sent WhatsApp message to {contact}."
            except Exception as e:
                app_logger.error(f"Failed to send message: {e}")
                return f"Failed to send message: {e}"
                
        if intent == "transfer_file":
            try:
                filename = entity
                import os
                import glob
                user_profile = os.environ.get("USERPROFILE", "C:\\Users\\Jainam Jain")
                search_dirs = [
                    os.path.join(user_profile, "Desktop"),
                    os.path.join(user_profile, "Downloads"),
                    os.path.join(user_profile, "Documents")
                ]
                
                found_path = None
                for d in search_dirs:
                    pattern = os.path.join(d, "**", filename)
                    matches = glob.glob(pattern, recursive=True)
                    if matches:
                        found_path = matches[0]
                        break
                        
                if not found_path:
                    # Try a broader search if not found
                    return f"Could not find file '{filename}' in Desktop, Downloads, or Documents."
                    
                app_logger.info(f"[{target}] Pushing file {found_path} to device")
                result = subprocess.run([self.adb_path, "-s", target, "push", found_path, "/sdcard/Download/"], capture_output=True, text=True)
                if result.returncode == 0:
                    return f"Successfully transferred {filename} to your phone's Download folder."
                else:
                    return f"Failed to transfer file: {result.stderr}"
            except Exception as e:
                app_logger.error(f"Failed to transfer file: {e}")
                return f"Failed to transfer file: {e}"
                
        if intent == "lock_phone":
            try:
                subprocess.run([self.adb_path, "-s", target, "shell", "input", "keyevent", "26"])
                return "I have locked your phone screen."
            except Exception as e:
                return f"Failed to lock phone: {e}"
        
        return f"Unknown intent: {intent}"
