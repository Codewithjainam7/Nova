import json
import os
import sys
import time
import subprocess
from typing import Dict, Any, Optional
from backend.core.logger import app_logger

# Ensure all ADB and device commands run completely silent without flashing a console window on Windows
_orig_subprocess_run = subprocess.run
def _silent_subprocess_run(cmd, *args, **kwargs):
    if sys.platform == 'win32' and 'creationflags' not in kwargs:
        kwargs['creationflags'] = 0x08000000
    return _orig_subprocess_run(cmd, *args, **kwargs)
subprocess.run = _silent_subprocess_run

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
            result = subprocess.run([self.adb_path, "connect", ip_port], capture_output=True, text=True, timeout=6)
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

    def discover_and_reconnect(self) -> list:
        """Attempts to reconnect to known devices, or scans local subnet/ARP table for Android devices on port 5555."""
        # 1. Try known devices first
        for dev in list(self.connected_devices):
            if ":" in dev:
                if self.connect(dev):
                    active = self.get_connected_devices(auto_discover=False)
                    if active:
                        return active

        # 2. Dynamic local subnet discovery via ARP table
        try:
            import socket
            res = subprocess.run(["arp", "-a"], capture_output=True, text=True, timeout=2)
            candidates = []
            for line in res.stdout.splitlines():
                parts = line.split()
                if len(parts) >= 2 and ("dynamic" in line.lower() or "192.168." in line):
                    ip = parts[0].strip()
                    if ip.startswith("192.168.") and not ip.endswith(".1") and not ip.endswith(".255"):
                        candidates.append(ip)

            for ip in candidates:
                s = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
                s.settimeout(0.3)
                is_open = (s.connect_ex((ip, 5555)) == 0)
                s.close()
                if is_open:
                    target = f"{ip}:5555"
                    if self.connect(target):
                        app_logger.info(f"[Auto-Discovery] Re-discovered Android phone at {target}")
                        active = self.get_connected_devices(auto_discover=False)
                        if active:
                            return active
        except Exception as e:
            app_logger.debug(f"Auto-discovery scan exception: {e}")

        return []

    def get_connected_devices(self, auto_discover: bool = True) -> list:
        try:
            result = subprocess.run([self.adb_path, "devices"], capture_output=True, text=True)
            devices = []
            for line in result.stdout.splitlines()[1:]:
                if "device" in line and "offline" not in line and "unauthorized" not in line:
                    parts = line.split('\t')
                    if len(parts) > 0:
                        devices.append(parts[0].strip())
            if devices:
                return devices
        except Exception:
            pass

        if auto_discover:
            return self.discover_and_reconnect()
        return []

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

    def is_locked(self, target: str) -> bool:
        """Returns True if the device screen is off, dozing, or showing keyguard/lockscreen."""
        try:
            res_p = subprocess.run([self.adb_path, "-s", target, "shell", "dumpsys", "power"], capture_output=True, text=True, timeout=5)
            if "mWakefulness=Awake" not in res_p.stdout:
                return True
            res_k = subprocess.run([self.adb_path, "-s", target, "shell", "dumpsys", "window", "policy"], capture_output=True, text=True, timeout=5)
            if "showing=true" in res_k.stdout:
                return True
            res_f = subprocess.run([self.adb_path, "-s", target, "shell", "dumpsys", "window", "displays"], capture_output=True, text=True, timeout=5)
            for line in res_f.stdout.splitlines():
                if "mCurrentFocus" in line:
                    if any(k in line for k in ["NotificationShade", "Keyguard", "StatusBar"]):
                        return True
        except Exception as e:
            app_logger.warning(f"Error checking lock state: {e}")
        return False

    def unlock_device(self, target: str):
        """Wakes up and unlocks an Android device if locked."""
        try:
            if not self.is_locked(target):
                app_logger.info(f"[{target}] Device already awake and unlocked.")
                return

            app_logger.info(f"[{target}] Device is locked/sleeping. Initiating wake and unlock...")
            res_p = subprocess.run([self.adb_path, "-s", target, "shell", "dumpsys", "power"], capture_output=True, text=True, timeout=5)
            if "mWakefulness=Awake" not in res_p.stdout:
                subprocess.run([self.adb_path, "-s", target, "shell", "input", "keyevent", "26"], timeout=5)
                import time
                time.sleep(1.0)
                
            # Swipe up to show PIN pad
            subprocess.run([self.adb_path, "-s", target, "shell", "input", "swipe", "500", "1800", "500", "500", "200"], timeout=5)
            import time
            time.sleep(1.0)
            
            pin = os.getenv("ANDROID_PIN", "860000")
            if pin:
                subprocess.run([self.adb_path, "-s", target, "shell", "input", "text", pin], timeout=5)
                time.sleep(0.5)
                subprocess.run([self.adb_path, "-s", target, "shell", "input", "keyevent", "66"], timeout=5)
                time.sleep(1.5)
            app_logger.info(f"[{target}] Unlock sequence completed.")
        except Exception as e:
            app_logger.error(f"Failed to unlock device: {e}")

    def dump_ui(self, target: str):
        """Dumps current on-screen UI hierarchy directly via exec-out and returns parsed ElementTree root."""
        try:
            res = subprocess.run([self.adb_path, "-s", target, "exec-out", "uiautomator", "dump", "/dev/tty"], capture_output=True, timeout=8)
            xml_bytes = res.stdout
            if xml_bytes and b"</hierarchy>" in xml_bytes:
                xml_bytes = xml_bytes[:xml_bytes.rfind(b"</hierarchy>") + len(b"</hierarchy>")]
                import xml.etree.ElementTree as ET
                return ET.fromstring(xml_bytes)
        except Exception as e:
            app_logger.warning(f"Fast dump_ui failed: {e}. Trying fallback...")
            
        try:
            subprocess.run([self.adb_path, "-s", target, "shell", "uiautomator", "dump", "/sdcard/ui_dump.xml"], capture_output=True, timeout=8)
            res2 = subprocess.run([self.adb_path, "-s", target, "shell", "cat", "/sdcard/ui_dump.xml"], capture_output=True, timeout=5)
            if res2.stdout and b"</hierarchy>" in res2.stdout:
                import xml.etree.ElementTree as ET
                return ET.fromstring(res2.stdout)
        except Exception as e:
            app_logger.warning(f"Fallback dump_ui failed: {e}")
        return None

    def get_node_center(self, node) -> Optional[tuple]:
        """Calculates center (x, y) coordinates from a node's bounds='[x1,y1][x2,y2]'."""
        import re
        if node is None:
            return None
        bounds = node.get("bounds", "")
        m = re.match(r'\[(\d+),(\d+)\]\[(\d+),(\d+)\]', bounds)
        if m:
            x1, y1, x2, y2 = map(int, m.groups())
            return (x1 + x2) // 2, (y1 + y2) // 2
        return None

    def find_node_by_id(self, root, resource_id: str):
        """Finds first XML node with matching resource-id."""
        if root is None:
            return None
        for n in root.iter("node"):
            if n.get("resource-id") == resource_id:
                return n
        return None

    def resolve_contact(self, contact: str, app: str = "whatsapp") -> str:
        """Resolves saved aliases for contacts (e.g. Manav -> Vedya on WhatsApp, Nandini -> Heera on Instagram)."""
        if not contact:
            return contact
        contacts_file = os.path.join(os.path.dirname(__file__), "known_contacts.json")
        if os.path.exists(contacts_file):
            try:
                with open(contacts_file, "r", encoding="utf-8") as f:
                    data = json.load(f)
                    c_lower = contact.strip().lower()
                    if c_lower in data:
                        mapping = data[c_lower]
                        if isinstance(mapping, dict):
                            app_clean = app.lower().strip()
                            if app_clean in ["instagram", "insta"]:
                                resolved = mapping.get("instagram", contact)
                            elif app_clean in ["whatsapp"]:
                                resolved = mapping.get("whatsapp", mapping.get("default", contact))
                            else:
                                resolved = mapping.get(app_clean, mapping.get("default", contact))
                            app_logger.info(f"Resolved contact alias: '{contact}' -> '{resolved}' for {app}")
                            return resolved
                        elif isinstance(mapping, str):
                            app_logger.info(f"Resolved contact alias: '{contact}' -> '{mapping}'")
                            return mapping
            except Exception as e:
                app_logger.warning(f"Error reading known_contacts.json: {e}")
        return contact

    def _sanitize_adb_text(self, text: str) -> str:
        """Sanitizes text for ADB shell input command, preserving capitalization, commas, and punctuation."""
        replacements = {
            '’': "'", '‘': "'", '“': '"', '”': '"',
            '—': '-', '–': '-', '…': '...'
        }
        for orig, rep in replacements.items():
            text = text.replace(orig, rep)
        
        clean = "".join([c for c in text if 32 <= ord(c) < 127])
        escaped = ""
        for ch in clean:
            if ch == " ":
                escaped += "%s"
            elif ch in ['\\', '"', "'", '?', '!', '&', ';', '(', ')', '<', '>', '|', '$', '`', '#', '*', '~']:
                escaped += f"\\{ch}"
            else:
                escaped += ch
        return escaped

    def get_foreground_app(self, target: str) -> str:
        """Returns the package name of the currently visible and focused application window."""
        try:
            res = subprocess.run(
                [self.adb_path, "-s", target, "shell", "dumpsys", "window", "displays"],
                capture_output=True, text=True, timeout=5
            )
            for line in res.stdout.splitlines():
                if "mCurrentFocus" in line:
                    import re
                    m = re.search(r'Window\{[0-9a-fA-F]+\s+u\d+\s+([a-zA-Z0-9_\.]+)', line)
                    if m:
                        return m.group(1)
                    if any(k in line for k in ["NotificationShade", "Keyguard", "StatusBar"]):
                        return "com.android.systemui"
            
            res_top = subprocess.run(
                [self.adb_path, "-s", target, "shell", "dumpsys", "activity", "top"],
                capture_output=True, text=True, timeout=5
            )
            for line in res_top.stdout.splitlines():
                line = line.strip()
                if line.startswith("ACTIVITY "):
                    parts = line.split()
                    if len(parts) >= 2:
                        return parts[1].split("/")[0]
        except Exception as e:
            app_logger.warning(f"Failed to get foreground app: {e}")
        return ""

    def ensure_foreground_app(self, target: str, package: str, max_retries: int = 3) -> bool:
        """
        State Awareness Guard:
        Verifies if the specified package is actively in the foreground.
        If the user closed it, pressed home, or switched apps, ADA automatically
        re-launches or brings it back to the foreground before performing any input.
        """
        import time
        for attempt in range(max_retries):
            fg = self.get_foreground_app(target)
            if package in fg:
                return True
            app_logger.info(f"Target app '{package}' not in foreground (currently '{fg}'). Restoring app to foreground (attempt {attempt+1}/{max_retries})...")
            # Wake and unlock if needed
            self.unlock_device(target)
            # Re-launch package
            subprocess.run(
                [self.adb_path, "-s", target, "shell", "monkey", "-p", package, "-c", "android.intent.category.LAUNCHER", "1"],
                capture_output=True, text=True, timeout=10
            )
            time.sleep(2.0)
        return package in self.get_foreground_app(target)

    def hide_keyboard_if_shown(self, target: str):
        """Dismisses the on-screen soft keyboard if active so UI buttons are not obscured by the keyboard's Next Line key."""
        try:
            for _ in range(2):
                res = subprocess.run([self.adb_path, "-s", target, "shell", "dumpsys", "input_method"], capture_output=True, text=True, timeout=5, encoding="utf-8", errors="replace")
                if res.stdout and "mInputShown=true" in res.stdout:
                    # In Android, when the IME soft keyboard is shown, keyevent 4 (BACK) is consumed
                    # exclusively by the IME to close itself, without popping the activity.
                    subprocess.run([self.adb_path, "-s", target, "shell", "input", "keyevent", "4"], timeout=5)
                    time.sleep(0.5)
                else:
                    break
        except Exception as e:
            app_logger.warning(f"Failed to hide soft keyboard: {e}")

    def _open_whatsapp_chat(self, target: str, contact: str, max_attempts: int = 4) -> bool:
        """
        State-Aware Self-Healing Navigator:
        Ensures WhatsApp is in the foreground and reliably navigates into the chat thread
        with the specified contact. Recovers gracefully if interrupted or minimized.
        """
        import time
        contact_clean = (contact or "").strip()
        if not contact_clean:
            app_logger.warning("[WhatsApp] Refusing navigation: Contact name is empty.")
            return False

        package = "com.whatsapp"
        
        for attempt in range(max_attempts):
            if not self.ensure_foreground_app(target, package):
                app_logger.warning(f"Attempt {attempt+1}: WhatsApp not in foreground.")
                time.sleep(1.0)
                continue
                
            ui_state = self.dump_ui(target)
            if ui_state is None:
                time.sleep(1.0)
                continue
                
            # State 1: Are we ALREADY in the correct chat thread?
            chat_name_node = self.find_node_by_id(ui_state, "com.whatsapp:id/conversation_contact_name")
            if chat_name_node is not None:
                chat_name = chat_name_node.get("text", "")
                if contact.lower() in chat_name.lower():
                    app_logger.info(f"Confirmed in chat thread with '{chat_name}'.")
                    return True
                else:
                    # In someone else's chat thread! Safely back out to chat list
                    app_logger.info(f"Currently in chat with '{chat_name}', expected '{contact}'. Pressing BACK...")
                    subprocess.run([self.adb_path, "-s", target, "shell", "input", "keyevent", "4"])
                    time.sleep(1.0)
                    continue

            # State 2: Are we in the Search Screen?
            search_input = self.find_node_by_id(ui_state, "com.whatsapp:id/search_input")
            if search_input is not None:
                app_logger.info(f"In WhatsApp Search screen. Typing contact '{contact}'...")
                contact_safe = self._sanitize_adb_text(contact)
                subprocess.run([self.adb_path, "-s", target, "shell", "input", "text", contact_safe])
                time.sleep(1.5)
                
                # Check search results
                ui_results = self.dump_ui(target)
                contact_target_node = None
                if ui_results is not None:
                    for node in ui_results.iter("node"):
                        txt = node.get("text", "")
                        desc = node.get("content-desc", "")
                        if contact.lower() in txt.lower() or contact.lower() in desc.lower():
                            contact_target_node = node
                            break
                    if contact_target_node is None:
                        contact_target_node = self.find_node_by_id(ui_results, "com.whatsapp:id/contact_row_container")
                
                if contact_target_node is not None:
                    coords = self.get_node_center(contact_target_node)
                    if coords:
                        subprocess.run([self.adb_path, "-s", target, "shell", "input", "tap", str(coords[0]), str(coords[1])])
                    else:
                        subprocess.run([self.adb_path, "-s", target, "shell", "input", "tap", "500", "610"])
                else:
                    subprocess.run([self.adb_path, "-s", target, "shell", "input", "tap", "500", "610"])
                time.sleep(1.5)
                
                # Verify we entered the chat thread
                ui_verify = self.dump_ui(target)
                if ui_verify is not None and self.find_node_by_id(ui_verify, "com.whatsapp:id/conversation_contact_name") is not None:
                    return True
                continue

            # State 3: Are we on WhatsApp Main Home / Chat List?
            # 3a: Check if contact is ALREADY visible in the active chat list!
            found_contact_node = None
            for node in ui_state.iter("node"):
                if node.get("resource-id") == "com.whatsapp:id/conversations_row_contact_name":
                    node_text = (node.get("text") or "").strip().lower()
                    if contact_clean.lower() in node_text:
                        found_contact_node = node
                        break
            
            if found_contact_node is not None:
                coords = self.get_node_center(found_contact_node)
                if coords:
                    app_logger.info(f"Contact '{contact_clean}' found directly on chat list at {coords}. Tapping...")
                    subprocess.run([self.adb_path, "-s", target, "shell", "input", "tap", str(coords[0]), str(coords[1])])
                    time.sleep(1.5)
                    ui_verify = self.dump_ui(target)
                    if ui_verify is not None and self.find_node_by_id(ui_verify, "com.whatsapp:id/conversation_contact_name") is not None:
                        return True
                    continue

            # 3b: Tap search bar
            search_bar = self.find_node_by_id(ui_state, "com.whatsapp:id/search_bar_inner_layout")
            if search_bar is not None:
                coords = self.get_node_center(search_bar)
                if coords:
                    subprocess.run([self.adb_path, "-s", target, "shell", "input", "tap", str(coords[0]), str(coords[1])])
                else:
                    subprocess.run([self.adb_path, "-s", target, "shell", "input", "tap", "617", "342"])
                time.sleep(1.2)
                continue

            # State 4: Unknown screen within WhatsApp -> Press BACK to recover to main home
            app_logger.info("WhatsApp in non-home state. Navigating back to home...")
            subprocess.run([self.adb_path, "-s", target, "shell", "input", "keyevent", "4"])
            time.sleep(1.0)
            
        return False

    def _open_instagram_chat(self, target: str, contact: str, max_attempts: int = 4) -> bool:
        """
        State-Aware Self-Healing Navigator for Instagram:
        Ensures Instagram is in foreground, navigates to Direct Inbox, searches or locates
        the contact chat, and enters the chat thread without any risk of opening Notifications.
        """
        import time
        contact_clean = (contact or "").strip()
        if not contact_clean:
            app_logger.warning("[Instagram] Refusing navigation: Contact name is empty.")
            return False

        package = "com.instagram.android"
        
        for attempt in range(max_attempts):
            if not self.ensure_foreground_app(target, package):
                app_logger.warning(f"Attempt {attempt+1}: Instagram not in foreground.")
                time.sleep(1.0)
                continue
                
            ui_state = self.dump_ui(target)
            if ui_state is None:
                time.sleep(1.0)
                continue

            # State 1: Are we ALREADY in a chat thread with the contact?
            composer = self.find_node_by_id(ui_state, "com.instagram.android:id/row_thread_composer_edittext")
            if composer is not None:
                for node in ui_state.iter("node"):
                    txt = node.get("text", "")
                    if contact.lower() in txt.lower():
                        app_logger.info(f"Confirmed in Instagram chat thread with '{contact}'.")
                        return True
                title_node = self.find_node_by_id(ui_state, "com.instagram.android:id/action_bar_title") or self.find_node_by_id(ui_state, "com.instagram.android:id/thread_title")
                if title_node is not None:
                    t_txt = title_node.get("text", "")
                    if contact.lower() in t_txt.lower():
                        app_logger.info(f"Confirmed in Instagram chat thread with '{t_txt}'.")
                        return True
                    else:
                        app_logger.info(f"Currently in chat with '{t_txt}', expected '{contact}'. Pressing BACK...")
                        subprocess.run([self.adb_path, "-s", target, "shell", "input", "keyevent", "4"])
                        time.sleep(1.0)
                        continue
                return True

            # State 2: Are we in the "New Message" search screen?
            new_msg_search = self.find_node_by_id(ui_state, "com.instagram.android:id/search_edit_text")
            if new_msg_search is not None:
                app_logger.info(f"In Instagram New Message screen. Typing contact '{contact}'...")
                coords = self.get_node_center(new_msg_search)
                if coords:
                    subprocess.run([self.adb_path, "-s", target, "shell", "input", "tap", str(coords[0]), str(coords[1])])
                    time.sleep(0.5)
                contact_safe = self._sanitize_adb_text(contact)
                subprocess.run([self.adb_path, "-s", target, "shell", "input", "text", contact_safe])
                time.sleep(2.0)
                
                ui_results = self.dump_ui(target)
                if ui_results is not None:
                    target_row = None
                    for node in ui_results.iter("node"):
                        txt = node.get("text", "")
                        desc = node.get("content-desc", "")
                        if contact.lower() in txt.lower() or contact.lower() in desc.lower():
                            if node.get("resource-id") in ["com.instagram.android:id/row_user_primary_name", "com.instagram.android:id/row_user_secondary_name"]:
                                target_row = node
                                break
                    if target_row is not None:
                        coords = self.get_node_center(target_row)
                        if coords:
                            subprocess.run([self.adb_path, "-s", target, "shell", "input", "tap", str(coords[0]), str(coords[1])])
                            time.sleep(1.5)
                            return True
                continue

            # State 3: Are we in Instagram Direct Inbox?
            inbox_bar = self.find_node_by_id(ui_state, "com.instagram.android:id/direct_inbox_action_bar")
            new_msg_btn = None
            for node in ui_state.iter("node"):
                if node.get("content-desc") == "New Message":
                    new_msg_btn = node
                    break
                    
            if inbox_bar is not None or new_msg_btn is not None:
                # 3a: Check if contact is ALREADY in the active DM inbox list!
                for node in ui_state.iter("node"):
                    txt = node.get("text", "")
                    if contact.lower() in txt.lower() and node.get("resource-id") in ["com.instagram.android:id/row_inbox_username", "com.instagram.android:id/row_inbox_digest"]:
                        coords = self.get_node_center(node)
                        if coords:
                            app_logger.info(f"Contact '{contact}' found directly in DM inbox list at {coords}. Tapping...")
                            subprocess.run([self.adb_path, "-s", target, "shell", "input", "tap", str(coords[0]), str(coords[1])])
                            time.sleep(1.5)
                            return True
                            
                # 3b: Tap 'New Message' button
                if new_msg_btn is not None:
                    coords = self.get_node_center(new_msg_btn)
                    if coords:
                        app_logger.info(f"Tapping New Message button at {coords}...")
                        subprocess.run([self.adb_path, "-s", target, "shell", "input", "tap", str(coords[0]), str(coords[1])])
                        time.sleep(1.5)
                        continue

            # State 4: On Instagram Home Feed or other tab? Look for direct_tab on bottom bar
            direct_tab = self.find_node_by_id(ui_state, "com.instagram.android:id/direct_tab")
            if direct_tab is not None:
                coords = self.get_node_center(direct_tab)
                if coords:
                    app_logger.info(f"Tapping Direct tab on bottom bar at {coords}...")
                    subprocess.run([self.adb_path, "-s", target, "shell", "input", "tap", str(coords[0]), str(coords[1])])
                    time.sleep(1.5)
                    continue

            # Fallback: Launch Direct Inbox intent
            app_logger.info("Launching instagram://direct-inbox intent...")
            subprocess.run([self.adb_path, "-s", target, "shell", "am", "start", "-a", "android.intent.action.VIEW", "-d", "instagram://direct-inbox"])
            time.sleep(2.0)
            
        return False

    def execute_action(self, intent: str, entity: str, **kwargs) -> str:
        """Executes a semantic action on the primary connected device."""
        active_devices = self.get_connected_devices()
        
        if not active_devices:
            active_devices = self.discover_and_reconnect()

        if not active_devices:
            return "Cannot execute action. No phone is currently connected. Please ensure Wireless Debugging is active or connect via USB."
            
        target = active_devices[0]
        
        # Ensure connected
        if ":" in target:
            success = self.connect(target)
            if not success:
                active_devices = self.discover_and_reconnect()
                if active_devices:
                    target = active_devices[0]
                else:
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
                "downloads": "com.android.providers.downloads.ui",
                "instagram": "com.instagram.android",
                "whatsapp": "com.whatsapp",
                "telegram": "org.telegram.messenger"
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
                contact = (entity or "").strip()
                if not contact:
                    app_logger.warning(f"[{target}] send_message rejected: No recipient contact specified.")
                    return "Cannot send message: No recipient contact was specified."

                self.unlock_device(target)
                message = kwargs.get("message", "")
                raw_app = kwargs.get("app", "whatsapp")
                app = raw_app.lower() if raw_app else "whatsapp"
                if not app or app in ["messaging", "phone", "default", "none"]:
                    app = "whatsapp"
                
                pkg_map = {
                    "whatsapp": "com.whatsapp",
                    "telegram": "org.telegram.messenger",
                    "instagram": "com.instagram.android"
                }
                package = pkg_map.get(app, "com.whatsapp")
                
                app_logger.info(f"[{target}] State-Aware {app} message to '{contact}': {message}")
                import time
                
                # Step 1: Ensure target app is launched and focused
                if not self.ensure_foreground_app(target, package):
                    return f"Failed to bring {app.capitalize()} to foreground on phone."
                time.sleep(1.0)
                
                if app == "telegram":
                    # Tap Search Icon (Top Right)
                    subprocess.run([self.adb_path, "-s", target, "shell", "input", "tap", "950", "150"])
                    time.sleep(1.0)
                    
                    self.ensure_foreground_app(target, package)
                    contact_safe = self._sanitize_adb_text(contact)
                    subprocess.run([self.adb_path, "-s", target, "shell", "input", "text", contact_safe])
                    time.sleep(2.0)
                    
                    subprocess.run([self.adb_path, "-s", target, "shell", "input", "keyevent", "4"])
                    time.sleep(1.0)
                    
                    self.ensure_foreground_app(target, package)
                    subprocess.run([self.adb_path, "-s", target, "shell", "input", "tap", "500", "350"])
                    time.sleep(1.5)
                    
                    self.ensure_foreground_app(target, package)
                    message_safe = self._sanitize_adb_text(message)
                    subprocess.run([self.adb_path, "-s", target, "shell", "input", "text", message_safe], timeout=15)
                    time.sleep(1.5)
                    
                    subprocess.run([self.adb_path, "-s", target, "shell", "input", "keyevent", "4"])
                    time.sleep(1.0)
                    
                    subprocess.run([self.adb_path, "-s", target, "shell", "input", "tap", "980", "2250"])
                    time.sleep(1.0)
                    return f"Successfully sent Telegram message to {contact}."

                elif app == "instagram":
                    resolved_contact = self.resolve_contact(contact, "instagram")
                    app_logger.info(f"[{target}] Navigating to Instagram chat with '{resolved_contact}'...")
                    
                    chat_ready = self._open_instagram_chat(target, resolved_contact)
                    if not chat_ready:
                        return f"Failed to locate or open Instagram chat for {resolved_contact}."

                    if not self.ensure_foreground_app(target, package):
                        return "Interrupted: Instagram lost focus."

                    # Find composer edittext
                    ui_chat = self.dump_ui(target)
                    composer = self.find_node_by_id(ui_chat, "com.instagram.android:id/row_thread_composer_edittext") if ui_chat is not None else None
                    if composer is not None:
                        coords = self.get_node_center(composer)
                        if coords:
                            subprocess.run([self.adb_path, "-s", target, "shell", "input", "tap", str(coords[0]), str(coords[1])])
                    else:
                        subprocess.run([self.adb_path, "-s", target, "shell", "input", "tap", "382", "2300"])
                    time.sleep(0.8)

                    if not self.ensure_foreground_app(target, package):
                        return "Interrupted: Instagram lost focus."

                    # Type the message
                    message_safe = self._sanitize_adb_text(message)
                    subprocess.run([self.adb_path, "-s", target, "shell", "input", "text", message_safe], timeout=15)
                    time.sleep(1.0)

                    # Hide keyboard
                    self.hide_keyboard_if_shown(target)
                    time.sleep(0.8)

                    if not self.ensure_foreground_app(target, package):
                        return "Interrupted: Instagram lost focus."

                    # Find and tap Send button
                    ui_send = self.dump_ui(target)
                    send_btn = None
                    if ui_send is not None:
                        send_btn = self.find_node_by_id(ui_send, "com.instagram.android:id/row_thread_composer_send_button_background")
                        if send_btn is None:
                            for node in ui_send.iter("node"):
                                if node.get("content-desc") == "Send" or node.get("text") == "Send":
                                    send_btn = node
                                    break
                    if send_btn is not None:
                        coords = self.get_node_center(send_btn)
                        if coords:
                            subprocess.run([self.adb_path, "-s", target, "shell", "input", "tap", str(coords[0]), str(coords[1])])
                    else:
                        subprocess.run([self.adb_path, "-s", target, "shell", "input", "tap", "988", "2300"])
                    time.sleep(1.0)
                    return f"Successfully sent Instagram message to {resolved_contact}."

                else:
                    # Default to WhatsApp
                    # Resolve contact alias (e.g. Manav -> Vedya)
                    resolved_contact = self.resolve_contact(contact, "whatsapp")
                    app_logger.info(f"[{target}] Navigating to WhatsApp chat with '{resolved_contact}'...")
                    
                    # State-Aware Self-Healing Navigation into Chat
                    chat_ready = self._open_whatsapp_chat(target, resolved_contact)
                    if not chat_ready:
                        return f"Failed to locate or open WhatsApp chat for {resolved_contact}."

                    # Verify still in foreground
                    if not self.ensure_foreground_app(target, package):
                        return "Interrupted: WhatsApp lost focus."

                    # Tap message entry composer (center: 329, 2321) - verified node com.whatsapp:id/entry
                    subprocess.run([self.adb_path, "-s", target, "shell", "input", "tap", "329", "2321"])
                    time.sleep(0.5)

                    # Guard: verify STILL focused before typing
                    if not self.ensure_foreground_app(target, package):
                        return "Interrupted: WhatsApp lost focus."

                    # Type the message
                    message_safe = self._sanitize_adb_text(message)
                    subprocess.run([self.adb_path, "-s", target, "shell", "input", "text", message_safe], timeout=15)
                    time.sleep(1.0)

                    # Dismiss soft keyboard so its Return/Next Line key does not intercept Send tap
                    self.hide_keyboard_if_shown(target)
                    time.sleep(0.8)

                    # Verify STILL focused before sending
                    if not self.ensure_foreground_app(target, package):
                        return "Interrupted: WhatsApp lost focus."

                    # Tap Send Button (center: 988, 2319) - verified node com.whatsapp:id/send_container
                    subprocess.run([self.adb_path, "-s", target, "shell", "input", "tap", "988", "2319"])
                    time.sleep(1.0)

                    return f"Successfully sent WhatsApp message to {resolved_contact}."
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
                
        if intent in ["lock_phone", "lock", "lock_mobile", "screen_off"]:
            try:
                subprocess.run([self.adb_path, "-s", target, "shell", "input", "keyevent", "26"])
                return "I have locked your phone screen."
            except Exception as e:
                return f"Failed to lock phone: {e}"

        if intent in ["unlock_phone", "unlock", "wake_phone", "screen_on"]:
            try:
                self.unlock_device(target)
                return "I have unlocked your phone."
            except Exception as e:
                return f"Failed to unlock phone: {e}"
        
        return f"Unknown intent: {intent}"
