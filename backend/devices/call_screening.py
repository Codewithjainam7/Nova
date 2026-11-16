import asyncio
import os
import re
import time
import json
import subprocess
from typing import Optional, Dict, Any, List, Callable
from backend.core.logger import app_logger

class CallScreeningDaemon:
    """
    Autonomous Mobile Telephony Guardian for ADA.
    Monitors Android telephony state via ADB, detects incoming calls,
    resolves caller identities from the Android Contacts Provider,
    and automatically answers/screens calls when the user is unavailable.
    """

    def __init__(self, adb_path: Optional[str] = None):
        if not adb_path:
            project_root = os.path.dirname(os.path.dirname(os.path.dirname(__file__)))
            self.adb_path = os.path.join(project_root, "platform-tools", "adb.exe")
        else:
            self.adb_path = adb_path

        self.enabled: bool = True
        self.unattended_seconds: float = 8.0  # Auto-answer threshold (~2-3 rings)
        self.is_monitoring: bool = False
        self._monitor_task: Optional[asyncio.Task] = None
        
        # Call State Tracking
        self.current_state: int = 0  # 0=IDLE, 1=RINGING, 2=OFFHOOK
        self.ringing_start_time: Optional[float] = None
        self.active_caller_number: Optional[str] = None
        self.active_caller_name: Optional[str] = None
        self.call_screened: bool = False
        
        # Call history log
        self.log_file = os.path.join(os.path.dirname(__file__), "call_screening_logs.json")
        self.event_callbacks: List[Callable[[Dict[str, Any]], None]] = []

    def register_callback(self, cb: Callable[[Dict[str, Any]], None]):
        self.event_callbacks.append(cb)

    def _notify(self, event_type: str, data: Dict[str, Any]):
        payload = {"event": event_type, "timestamp": time.time(), **data}
        for cb in self.event_callbacks:
            try:
                cb(payload)
            except Exception as e:
                app_logger.warning(f"[CallScreening] Callback error: {e}")

    def _get_target_device(self) -> Optional[str]:
        try:
            res = subprocess.run([self.adb_path, "devices"], capture_output=True, text=True, timeout=3)
            for line in res.stdout.splitlines():
                if "\tdevice" in line:
                    return line.split("\t")[0]
        except Exception:
            pass
        return None

    def resolve_caller_name(self, target: str, phone_number: str) -> str:
        """Resolves caller number against Android's internal contacts provider."""
        if not phone_number:
            return "Unknown Caller"
            
        clean_num = re.sub(r'[^\d+]', '', phone_number)
        
        # 1. Query Android Contacts Provider
        try:
            res = subprocess.run(
                [self.adb_path, "-s", target, "shell", "content", "query",
                 "--uri", "content://com.android.contacts/data/phones",
                 "--projection", "display_name:data1"],
                capture_output=True, text=True, timeout=4, errors="ignore"
            )
            for line in res.stdout.splitlines():
                if "display_name=" in line and "data1=" in line:
                    parts = line.split("display_name=")
                    if len(parts) > 1:
                        sub = parts[1].split(", data1=")
                        name = sub[0].strip()
                        num = re.sub(r'[^\d+]', '', sub[1].strip()) if len(sub) > 1 else ""
                        if clean_num and (clean_num in num or (len(clean_num) >= 7 and clean_num[-7:] in num)):
                            app_logger.info(f"[CallScreening] Resolved {phone_number} -> {name}")
                            return name
        except Exception as e:
            app_logger.debug(f"[CallScreening] Contacts query notice: {e}")

        # 2. Query known_contacts.json fallback
        try:
            known_path = os.path.join(os.path.dirname(__file__), "known_contacts.json")
            if os.path.exists(known_path):
                with open(known_path, "r", encoding="utf-8") as f:
                    data = json.load(f)
                    for alias, meta in data.items():
                        if isinstance(meta, dict) and meta.get("phone"):
                            if clean_num in re.sub(r'[^\d+]', '', meta["phone"]):
                                return alias.title()
        except Exception:
            pass

        return phone_number

    def read_telephony_state(self, target: str) -> Dict[str, Any]:
        """Polls dumpsys telephony.registry for accurate real-time call states across all SIM slots."""
        try:
            res = subprocess.run(
                [self.adb_path, "-s", target, "shell", "dumpsys", "telephony.registry"],
                capture_output=True, text=True, timeout=3, errors="ignore"
            )
            states = []
            incoming_numbers = []
            for line in res.stdout.splitlines():
                if "mCallState=" in line:
                    m = re.search(r'mCallState=(\d+)', line)
                    if m:
                        states.append(int(m.group(1)))
                if "mCallIncomingNumber=" in line:
                    m_num = re.search(r'mCallIncomingNumber=([^\s,]+)', line)
                    if m_num and m_num.group(1) and m_num.group(1).strip():
                        incoming_numbers.append(m_num.group(1).strip())

            # State priority across Dual SIM: 1 (RINGING) > 2 (OFFHOOK) > 0 (IDLE)
            active_state = 0
            if 1 in states:
                active_state = 1
            elif 2 in states:
                active_state = 2
            elif states:
                active_state = states[0]

            active_num = incoming_numbers[0] if incoming_numbers else ""
            return {"call_state": active_state, "incoming_number": active_num}
        except Exception as e:
            app_logger.debug(f"[CallScreening] Poll error: {e}")
            return {"call_state": 0, "incoming_number": ""}

    def answer_call(self, target: str):
        """Answers incoming call reliably on POCO X6 Neo 5G (HyperOS) and enables speakerphone."""
        app_logger.info(f"[CallScreening] Answering incoming call on {target}...")
        try:
            # 1. Wake screen up
            subprocess.run([self.adb_path, "-s", target, "shell", "input", "keyevent", "224"], timeout=2)
            time.sleep(0.3)
            # 2. Keyevent 79 (KEYCODE_HEADSETHOOK) & Keyevent 5 (KEYCODE_CALL) for HyperOS pickup
            subprocess.run([self.adb_path, "-s", target, "shell", "input", "keyevent", "79"], timeout=2)
            subprocess.run([self.adb_path, "-s", target, "shell", "input", "keyevent", "5"], timeout=2)
            time.sleep(1.2)
            # 3. Toggle speakerphone (Keyevent 226)
            subprocess.run([self.adb_path, "-s", target, "shell", "input", "keyevent", "226"], timeout=2)
            return True
        except Exception as e:
            app_logger.error(f"[CallScreening] Failed to answer call: {e}")
            return False

    def end_call(self, target: str):
        """Hangs up or rejects the current call."""
        app_logger.info(f"[CallScreening] Ending call on {target}...")
        try:
            # Keyevent 6 = KEYCODE_ENDCALL
            subprocess.run([self.adb_path, "-s", target, "shell", "input", "keyevent", "6"], timeout=3)
            return True
        except Exception as e:
            app_logger.error(f"[CallScreening] Failed to end call: {e}")
            return False

    async def play_ada_greeting(self, target: str, caller_name: str):
        """Generates ADA speech greeting and plays it out loud on phone speaker."""
        greeting_text = (
            f"Hello. This is ADA, Jainam's personal AI assistant. "
            f"Jainam is currently unavailable to take your call. "
            f"I have notified him that you reached out. Please leave a brief message, or he will call you back shortly."
        )
        
        # Synthesize via edge_tts
        try:
            import edge_tts
            communicate = edge_tts.Communicate(greeting_text, "en-GB-SoniaNeural")
            local_wav = os.path.join(os.path.dirname(__file__), "ada_call_greeting.mp3")
            await communicate.save(local_wav)
            
            # Push to phone sdcard
            subprocess.run([self.adb_path, "-s", target, "push", local_wav, "/sdcard/ada_greeting.mp3"], capture_output=True, timeout=5)
            
            # Play on phone
            subprocess.run(
                [self.adb_path, "-s", target, "shell", "am", "start", "-a", "android.intent.action.VIEW",
                 "-d", "file:///sdcard/ada_greeting.mp3", "-t", "audio/mp3"],
                capture_output=True, timeout=4
            )
            app_logger.info("[CallScreening] ADA greeting speech delivered to caller.")
        except Exception as e:
            app_logger.warning(f"[CallScreening] Speech playback notice: {e}")

    def log_call_event(self, caller: str, number: str, action: str, duration_sec: float = 0.0):
        record = {
            "timestamp": time.strftime("%Y-%m-%d %H:%M:%S"),
            "caller": caller,
            "number": number,
            "action": action,
            "duration_sec": round(duration_sec, 1)
        }
        records = []
        if os.path.exists(self.log_file):
            try:
                with open(self.log_file, "r", encoding="utf-8") as f:
                    records = json.load(f)
            except Exception:
                records = []
        records.insert(0, record)
        try:
            with open(self.log_file, "w", encoding="utf-8") as f:
                json.dump(records[:100], f, indent=2)
        except Exception:
            pass

    async def start_monitoring(self):
        """Starts real-time background call state monitoring loop."""
        if self.is_monitoring:
            return
        self.is_monitoring = True
        app_logger.info("[CallScreening] Autonomous Telephony Guardian started.")

        while self.is_monitoring:
            try:
                if not self.enabled:
                    await asyncio.sleep(2.0)
                    continue

                target = self._get_target_device()
                if not target:
                    await asyncio.sleep(3.0)
                    continue

                state_info = await asyncio.to_thread(self.read_telephony_state, target)
                call_state = state_info["call_state"]
                num = state_info["incoming_number"]

                # State 1: RINGING
                if call_state == 1:
                    if self.current_state != 1:
                        # New incoming call detected!
                        self.current_state = 1
                        self.ringing_start_time = time.time()
                        self.call_screened = False
                        self.active_caller_number = num
                        self.active_caller_name = await asyncio.to_thread(self.resolve_caller_name, target, num)
                        
                        app_logger.info(f"[CallScreening] INCOMING CALL DETECTED: {self.active_caller_name} ({num})")
                        self._notify("INCOMING_CALL", {
                            "caller_name": self.active_caller_name,
                            "caller_number": num,
                            "ringing_time": 0
                        })

                    else:
                        # Call is still ringing; check if unattended threshold passed
                        elapsed = time.time() - (self.ringing_start_time or time.time())
                        if elapsed >= self.unattended_seconds and not self.call_screened:
                            # User hasn't answered -> ADA steps in to autonomously screen the call!
                            self.call_screened = True
                            app_logger.info(f"[CallScreening] Call unattended for {elapsed:.1f}s. ADA auto-screening initiated!")
                            
                            self._notify("SCREENING_INITIATED", {
                                "caller_name": self.active_caller_name,
                                "caller_number": self.active_caller_number,
                                "elapsed": elapsed
                            })

                            # Answer the call
                            await asyncio.to_thread(self.answer_call, target)
                            await asyncio.sleep(1.5)

                            # Deliver ADA speech
                            await self.play_ada_greeting(target, self.active_caller_name or "Caller")
                            await asyncio.sleep(8.0)

                            # Hang up gracefully
                            await asyncio.to_thread(self.end_call, target)
                            self.log_call_event(
                                caller=self.active_caller_name or "Unknown",
                                number=self.active_caller_number or "",
                                action="AUTO_SCREENED_BY_ADA",
                                duration_sec=elapsed + 9.5
                            )

                            self._notify("CALL_SCREENED", {
                                "caller_name": self.active_caller_name,
                                "action": "AUTO_SCREENED_BY_ADA"
                            })

                # State 2: OFFHOOK (User answered manually or in active call)
                elif call_state == 2:
                    if self.current_state == 1 and not self.call_screened:
                        app_logger.info("[CallScreening] User picked up call manually.")
                        self.log_call_event(
                            caller=self.active_caller_name or "Unknown",
                            number=self.active_caller_number or "",
                            action="USER_ANSWERED"
                        )
                        self._notify("USER_ANSWERED", {"caller_name": self.active_caller_name})
                    self.current_state = 2

                # State 0: IDLE (Call ended or no call)
                elif call_state == 0:
                    if self.current_state in [1, 2]:
                        app_logger.info("[CallScreening] Call completed/idle.")
                        self._notify("CALL_ENDED", {"caller_name": self.active_caller_name})
                    self.current_state = 0
                    self.ringing_start_time = None
                    self.active_caller_number = None
                    self.active_caller_name = None
                    self.call_screened = False

            except Exception as e:
                app_logger.debug(f"[CallScreening] Loop notice: {e}")

            await asyncio.sleep(0.8)

    def stop_monitoring(self):
        self.is_monitoring = False

# Global Singleton Instance
call_screener = CallScreeningDaemon()
