import asyncio
import os
import re
import time
import json
import subprocess
import urllib.request
import urllib.parse
from typing import Optional, Dict, Any, List, Callable
from backend.core.logger import app_logger

class CallScreeningDaemon:
    """
    Autonomous Mobile Telephony Guardian for ADA.
    Monitors Android telephony state via ADB on POCO X6 Neo 5G (HyperOS),
    auto-answers unattended calls, delivers conversational AI responses,
    captures native call recordings, generates AI conclusions via Groq/Gemini,
    and dispatches voice notes & executive summaries to Telegram.
    """

    def __init__(self, adb_path: Optional[str] = None):
        project_root = os.path.dirname(os.path.dirname(os.path.dirname(__file__)))
        if not adb_path:
            self.adb_path = os.path.join(project_root, "platform-tools", "adb.exe")
        else:
            self.adb_path = adb_path

        self.project_root = project_root
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
        
        # Local recording storage
        self.recordings_dir = os.path.join(os.path.dirname(__file__), "recordings")
        os.makedirs(self.recordings_dir, exist_ok=True)

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
        """Resolves caller number against Android Contacts Provider and known_contacts."""
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
        """Polls dumpsys telephony.registry for accurate real-time call states across Dual SIMs."""
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
            
            # 3. Maximize in-call voice volume
            subprocess.run([self.adb_path, "-s", target, "shell", "cmd", "audio", "set-volume", "0", "5"], timeout=2)
            subprocess.run([self.adb_path, "-s", target, "shell", "input", "keyevent", "24"], timeout=2)
            
            # 4. Enable speakerphone via InCallUI tap / keyevent
            self._activate_speakerphone_and_record(target)
            return True
        except Exception as e:
            app_logger.error(f"[CallScreening] Failed to answer call: {e}")
            return False

    def _activate_speakerphone_and_record(self, target: str):
        """Taps Speaker and Record buttons in InCallUI if present."""
        try:
            dump_res = subprocess.run([self.adb_path, "-s", target, "shell", "uiautomator", "dump", "/data/local/tmp/incall_ui.xml"], capture_output=True, timeout=3)
            xml_data = subprocess.run([self.adb_path, "-s", target, "shell", "cat", "/data/local/tmp/incall_ui.xml"], capture_output=True, text=True, errors="ignore").stdout
            
            # Look for Speaker button bounds
            speaker_match = re.search(r'content-desc="[^"]*[Ss]peaker[^"]*"[^>]*bounds="\[(\d+),(\d+)\]\[(\d+),(\d+)\]"', xml_data)
            if not speaker_match:
                speaker_match = re.search(r'text="[^"]*[Ss]peaker[^"]*"[^>]*bounds="\[(\d+),(\d+)\]\[(\d+),(\d+)\]"', xml_data)
                
            if speaker_match:
                x1, y1, x2, y2 = map(int, speaker_match.groups())
                tap_x = (x1 + x2) // 2
                tap_y = (y1 + y2) // 2
                subprocess.run([self.adb_path, "-s", target, "shell", "input", "tap", str(tap_x), str(tap_y)], timeout=2)
                app_logger.info(f"[CallScreening] Speakerphone activated via InCallUI tap at ({tap_x}, {tap_y})")
            else:
                # Default POCO X6 Neo 5G InCallUI Speaker coordinate fallback
                subprocess.run([self.adb_path, "-s", target, "shell", "input", "tap", "880", "1450"], timeout=2)

            time.sleep(0.5)
            # Look for Record button bounds in InCallUI
            rec_match = re.search(r'content-desc="[^"]*[Rr]ecord[^"]*"[^>]*bounds="\[(\d+),(\d+)\]\[(\d+),(\d+)\]"', xml_data)
            if rec_match:
                rx1, ry1, rx2, ry2 = map(int, rec_match.groups())
                rtap_x = (rx1 + rx2) // 2
                rtap_y = (ry1 + ry2) // 2
                subprocess.run([self.adb_path, "-s", target, "shell", "input", "tap", str(rtap_x), str(rtap_y)], timeout=2)
                app_logger.info(f"[CallScreening] Call Recording initiated via InCallUI at ({rtap_x}, {rtap_y})")
        except Exception as e:
            app_logger.debug(f"[CallScreening] InCallUI interaction notice: {e}")

    def end_call(self, target: str):
        """Hangs up the current call."""
        app_logger.info(f"[CallScreening] Ending call on {target}...")
        try:
            # Keyevent 6 = KEYCODE_ENDCALL
            subprocess.run([self.adb_path, "-s", target, "shell", "input", "keyevent", "6"], timeout=3)
            return True
        except Exception as e:
            app_logger.error(f"[CallScreening] Failed to end call: {e}")
            return False

    async def play_ada_speech(self, target: str, speech_text: str, filename: str = "ada_greeting.mp3"):
        """Synthesizes speech via edge_tts and plays it directly over phone speaker via native AudioPreview."""
        try:
            import edge_tts
            communicate = edge_tts.Communicate(speech_text, "en-GB-SoniaNeural")
            local_mp3 = os.path.join(self.recordings_dir, filename)
            await communicate.save(local_mp3)
            
            phone_dest = f"/sdcard/{filename}"
            # Push to phone
            subprocess.run([self.adb_path, "-s", target, "push", local_mp3, phone_dest], capture_output=True, timeout=5)
            
            # Play on phone using explicit MiUI AudioPreview component (bypasses ResolverActivity chooser)
            subprocess.run(
                [self.adb_path, "-s", target, "shell", "am", "start",
                 "-n", "com.miui.player/com.miui.player.phone.ui.AudioPreview",
                 "-a", "android.intent.action.VIEW",
                 "-d", f"file://{phone_dest}",
                 "-t", "audio/mp3"],
                capture_output=True, timeout=4
            )
            app_logger.info(f"[CallScreening] ADA speech delivered: '{speech_text[:50]}...'")
        except Exception as e:
            app_logger.warning(f"[CallScreening] Speech playback error: {e}")

    def fetch_latest_recording(self, target: str) -> Optional[str]:
        """Finds and pulls the newest call recording from POCO X6 Neo 5G."""
        search_dirs = [
            "/storage/emulated/0/Music/Recordings/Call Recordings",
            "/sdcard/Music/Recordings/Call Recordings",
            "/sdcard/MIUI/sound_recorder/call_rec"
        ]
        
        for sdir in search_dirs:
            try:
                res = subprocess.run([self.adb_path, "-s", target, "shell", f"ls -t '{sdir}' 2>/dev/null"], capture_output=True, text=True, timeout=4)
                files = [f.strip() for f in res.stdout.splitlines() if f.strip().endswith((".mp3", ".awb", ".m4a", ".wav", ".aac"))]
                if files:
                    newest = files[0]
                    phone_path = f"{sdir}/{newest}"
                    local_filename = f"call_{int(time.time())}_{newest}"
                    local_path = os.path.join(self.recordings_dir, local_filename)
                    subprocess.run([self.adb_path, "-s", target, "pull", phone_path, local_path], capture_output=True, timeout=10)
                    if os.path.exists(local_path) and os.path.getsize(local_path) > 0:
                        app_logger.info(f"[CallScreening] Successfully fetched call recording: {local_path}")
                        return local_path
            except Exception as e:
                app_logger.debug(f"[CallScreening] Fetch recording notice: {e}")
        return None

    def transcribe_with_groq(self, audio_file_path: str) -> str:
        """Transcribes call audio using Groq Whisper (whisper-large-v3-turbo) in ~150ms."""
        groq_api_key = os.getenv("GROQ_API_KEY", "")
        if not groq_api_key or not os.path.exists(audio_file_path):
            return "No audio recording available to transcribe."

        try:
            import mimetypes
            boundary = f"----WebKitFormBoundary{int(time.time())}"
            filename = os.path.basename(audio_file_path)
            content_type = mimetypes.guess_type(audio_file_path)[0] or "audio/mp3"

            with open(audio_file_path, "rb") as f:
                file_bytes = f.read()

            body = bytearray()
            # File field
            body.extend(f"--{boundary}\r\n".encode())
            body.extend(f'Content-Disposition: form-data; name="file"; filename="{filename}"\r\n'.encode())
            body.extend(f"Content-Type: {content_type}\r\n\r\n".encode())
            body.extend(file_bytes)
            body.extend(b"\r\n")

            # Model field
            body.extend(f"--{boundary}\r\n".encode())
            body.extend(b'Content-Disposition: form-data; name="model"\r\n\r\n')
            body.extend(b"whisper-large-v3-turbo\r\n")
            body.extend(f"--{boundary}--\r\n".encode())

            req = urllib.request.Request(
                "https://api.groq.com/openai/v1/audio/transcriptions",
                data=bytes(body),
                headers={
                    "Authorization": f"Bearer {groq_api_key}",
                    "Content-Type": f"multipart/form-data; boundary={boundary}",
                    "User-Agent": "ADA-Agent/1.0"
                }
            )

            with urllib.request.urlopen(req, timeout=15) as resp:
                result = json.loads(resp.read().decode())
                transcript = result.get("text", "").strip()
                app_logger.info(f"[CallScreening] Whisper Transcript: '{transcript}'")
                return transcript
        except Exception as e:
            app_logger.error(f"[CallScreening] Groq Whisper error: {e}")
            return "Transcription unavailable."

    def generate_ai_conclusion(self, caller: str, number: str, transcript: str) -> Dict[str, Any]:
        """Uses Gemini Flash or Groq Llama to generate a concise summary and action items."""
        groq_api_key = os.getenv("GROQ_API_KEY", "")
        prompt = (
            f"You are ADA, Jainam's personal AI executive assistant.\n"
            f"You just autonomously screened a phone call on his behalf.\n"
            f"Caller: {caller} ({number})\n"
            f"Transcript of what the caller said: \"{transcript}\"\n\n"
            f"Generate a clear, high-priority executive briefing in JSON format with exactly these keys:\n"
            f"- summary: 1-2 sentence concise explanation of why they called and what they said.\n"
            f"- urgency: Exactly one of ['LOW', 'MEDIUM', 'HIGH', 'CRITICAL'].\n"
            f"- action_required: Specific next step Jainam needs to take (e.g. 'Call Mom back before 7 PM regarding groceries').\n"
            f"Output ONLY valid JSON."
        )

        try:
            req = urllib.request.Request(
                "https://api.groq.com/openai/v1/chat/completions",
                data=json.dumps({
                    "model": "llama-3.3-70b-versatile",
                    "messages": [{"role": "user", "content": prompt}],
                    "temperature": 0.2,
                    "response_format": {"type": "json_object"}
                }).encode(),
                headers={
                    "Authorization": f"Bearer {groq_api_key}",
                    "Content-Type": "application/json",
                    "User-Agent": "ADA-Agent/1.0"
                }
            )
            with urllib.request.urlopen(req, timeout=10) as resp:
                data = json.loads(resp.read().decode())
                content = data["choices"][0]["message"]["content"]
                return json.loads(content)
        except Exception as e:
            app_logger.debug(f"[CallScreening] Conclusion generation error: {e}")
            return {
                "summary": f"{caller} called and left a voice message.",
                "urgency": "MEDIUM",
                "action_required": f"Review transcript and return call to {caller} ({number})."
            }

    def send_telegram_alert(self, caller: str, number: str, conclusion: Dict[str, Any], transcript: str, audio_path: Optional[str] = None):
        """Sends rich call briefing and playable audio file straight to Telegram."""
        bot_token = os.getenv("TELEGRAM_BOT_TOKEN", "").strip()
        chat_id = os.getenv("TELEGRAM_CHAT_ID", "").strip()

        if not bot_token or not chat_id:
            app_logger.info("[CallScreening] Telegram bot credentials not set in .env. Skipping Telegram alert.")
            return

        urgency_emoji = {
            "LOW": "🟢",
            "MEDIUM": "🟡",
            "HIGH": "🟠",
            "CRITICAL": "🔴"
        }.get(conclusion.get("urgency", "MEDIUM"), "🟡")

        msg_text = (
            f"🚨 *ADA Call Screening Alert*\n\n"
            f"👤 *Caller:* {caller} (`{number}`)\n"
            f"⏱ *Status:* Auto-Screened by ADA\n"
            f"{urgency_emoji} *Urgency:* {conclusion.get('urgency', 'MEDIUM')}\n\n"
            f"📌 *Executive Summary:*\n{conclusion.get('summary', 'No summary available.')}\n\n"
            f"⚡ *Action Required:*\n{conclusion.get('action_required', 'None specified.')}\n\n"
            f"📄 *Transcript:*\n_{transcript}_"
        )

        # 1. Send text message
        try:
            url = f"https://api.telegram.org/bot{bot_token}/sendMessage"
            payload = json.dumps({
                "chat_id": chat_id,
                "text": msg_text,
                "parse_mode": "Markdown"
            }).encode()
            req = urllib.request.Request(url, data=payload, headers={"Content-Type": "application/json"})
            with urllib.request.urlopen(req, timeout=8):
                pass
            app_logger.info("[CallScreening] Telegram briefing dispatched successfully.")
        except Exception as e:
            app_logger.error(f"[CallScreening] Failed to send Telegram text alert: {e}")

        # 2. Send audio recording file if available
        if audio_path and os.path.exists(audio_path):
            try:
                boundary = f"----WebKitBoundary{int(time.time())}"
                filename = os.path.basename(audio_path)
                with open(audio_path, "rb") as f:
                    audio_bytes = f.read()

                body = bytearray()
                # chat_id
                body.extend(f"--{boundary}\r\n".encode())
                body.extend(b'Content-Disposition: form-data; name="chat_id"\r\n\r\n')
                body.extend(f"{chat_id}\r\n".encode())
                # caption
                body.extend(f"--{boundary}\r\n".encode())
                body.extend(b'Content-Disposition: form-data; name="caption"\r\n\r\n')
                body.extend(f"🎙 Call Recording with {caller}\r\n".encode())
                # audio file
                body.extend(f"--{boundary}\r\n".encode())
                body.extend(f'Content-Disposition: form-data; name="audio"; filename="{filename}"\r\n'.encode())
                body.extend(b"Content-Type: audio/mpeg\r\n\r\n")
                body.extend(audio_bytes)
                body.extend(b"\r\n")
                body.extend(f"--{boundary}--\r\n".encode())

                url = f"https://api.telegram.org/bot{bot_token}/sendAudio"
                req = urllib.request.Request(url, data=bytes(body), headers={"Content-Type": f"multipart/form-data; boundary={boundary}"})
                with urllib.request.urlopen(req, timeout=20):
                    pass
                app_logger.info("[CallScreening] Telegram call audio recording sent successfully.")
            except Exception as e:
                app_logger.warning(f"[CallScreening] Failed to send Telegram audio note: {e}")

    def log_call_event(self, caller: str, number: str, action: str, duration_sec: float = 0.0, conclusion: Optional[Dict[str, Any]] = None, transcript: str = "", audio_file: str = ""):
        record = {
            "timestamp": time.strftime("%Y-%m-%d %H:%M:%S"),
            "caller": caller,
            "number": number,
            "action": action,
            "duration_sec": round(duration_sec, 1),
            "summary": conclusion.get("summary", "") if conclusion else "",
            "urgency": conclusion.get("urgency", "NORMAL") if conclusion else "NORMAL",
            "action_required": conclusion.get("action_required", "") if conclusion else "",
            "transcript": transcript,
            "audio_file": audio_file
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
        app_logger.info("[CallScreening] Autonomous Telephony Guardian started on POCO X6 Neo 5G.")

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

                            # 1. Answer call and activate speakerphone
                            await asyncio.to_thread(self.answer_call, target)
                            await asyncio.sleep(1.0)

                            # 2. Deliver personalized ADA introduction
                            c_name = self.active_caller_name if (self.active_caller_name and self.active_caller_name != self.active_caller_number) else "there"
                            
                            # Time-aware context
                            current_hour = time.localtime().tm_hour
                            if current_hour >= 23 or current_hour < 7:
                                status_context = "currently resting and away from his phone"
                            else:
                                status_context = "currently unavailable and away from his phone right now"

                            greeting = (
                                f"Hello {c_name}. This is ADA, Jainam's personal AI assistant. "
                                f"Jainam is {status_context}. "
                                f"Please leave a brief message or let me know if it's urgent, and I will ensure he receives your message immediately."
                            )
                            await self.play_ada_speech(target, greeting, "ada_greeting.mp3")
                            
                            # 3. Message listening buffer (giving caller 12 seconds to speak their message)
                            await asyncio.sleep(12.0)

                            # 4. Closing statement
                            closing = "Thank you. I have recorded your message and notified Jainam. Goodbye!"
                            await self.play_ada_speech(target, closing, "ada_closing.mp3")
                            await asyncio.sleep(3.5)

                            # 5. End call gracefully
                            await asyncio.to_thread(self.end_call, target)
                            call_duration = elapsed + 17.0

                            # 6. Post-Call Extraction & AI Processing
                            await asyncio.sleep(2.0)
                            rec_file = await asyncio.to_thread(self.fetch_latest_recording, target)
                            transcript = "Caller reached out while you were unavailable."
                            if rec_file:
                                transcript = await asyncio.to_thread(self.transcribe_with_groq, rec_file)

                            conclusion = await asyncio.to_thread(self.generate_ai_conclusion, self.active_caller_name or "Caller", self.active_caller_number or "", transcript)
                            
                            # 7. Dispatch to Telegram
                            await asyncio.to_thread(self.send_telegram_alert, self.active_caller_name or "Caller", self.active_caller_number or "", conclusion, transcript, rec_file)

                            # 8. Log and notify Dynamic Island
                            self.log_call_event(
                                caller=self.active_caller_name or "Unknown",
                                number=self.active_caller_number or "",
                                action="AUTO_SCREENED_BY_ADA",
                                duration_sec=call_duration,
                                conclusion=conclusion,
                                transcript=transcript,
                                audio_file=rec_file or ""
                            )

                            self._notify("CALL_SCREENED", {
                                "caller_name": self.active_caller_name,
                                "caller_number": self.active_caller_number,
                                "summary": conclusion.get("summary", ""),
                                "urgency": conclusion.get("urgency", "MEDIUM"),
                                "action_required": conclusion.get("action_required", ""),
                                "duration_sec": call_duration
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
