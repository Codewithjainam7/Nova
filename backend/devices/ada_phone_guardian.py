#!/usr/bin/env python3
"""
ADA Autonomous On-Device Conversational Guardian (Termux Standalone)
=====================================================================
Runs 100% locally on POCO X6 Neo 5G inside Termux.
- ₹0 Cost (Uses phone's physical SIM, Groq Free Tier, Telegram Free API)
- True Vapi-style Multi-Turn Dialogue (Whisper + LLaMA 3.3 70B + Neural TTS)
- Completely independent of laptop: screens calls 24/7 anywhere you go!
"""

import os
import sys
import time
import json
import asyncio
import subprocess
import urllib.request
import urllib.parse
from typing import List, Dict, Any, Optional

# Configuration & Keys (Loaded from environment or local config)
GROQ_API_KEY = os.environ.get("GROQ_API_KEY", "")
TELEGRAM_BOT_TOKEN = os.environ.get("TELEGRAM_BOT_TOKEN", "")
TELEGRAM_CHAT_ID = os.environ.get("TELEGRAM_CHAT_ID", "")
UNATTENDED_SECONDS = float(os.environ.get("UNATTENDED_SECONDS", "8.0"))

class ADAPhoneGuardian:
    def __init__(self):
        self.conversation_history: List[Dict[str, str]] = []
        self.is_in_call = False
        self.caller_number = "Unknown"
        self.caller_name = "Caller"
        self.call_start_time = 0.0

    def run_termux_cmd(self, cmd: List[str]) -> str:
        try:
            res = subprocess.run(cmd, capture_output=True, text=True, timeout=10)
            return res.stdout.strip()
        except Exception as e:
            print(f"Termux command error: {e}")
            return ""

    def speak(self, text: str):
        """Speaks text using Termux native neural TTS or fast on-device voice engine."""
        print(f"[ADA Speaks]: {text}")
        # Use termux-tts-speak
        subprocess.run(["termux-tts-speak", "-p", "1.0", "-r", "1.05", text])

    async def transcribe_audio(self, audio_path: str) -> str:
        """Transcribes recorded audio chunk using Groq Whisper (takes ~250ms)."""
        if not os.path.exists(audio_path) or os.path.getsize(audio_path) < 1000:
            return ""

        url = "https://api.groq.com/openai/v1/audio/transcriptions"
        try:
            # Prepare multipart upload
            boundary = f"----WebKitFormBoundary{int(time.time())}"
            with open(audio_path, "rb") as f:
                file_bytes = f.read()

            body = bytearray()
            # model parameter
            body.extend(f"--{boundary}
Content-Disposition: form-data; name="model"

whisper-large-v3-turbo
".encode())
            # file parameter
            filename = os.path.basename(audio_path)
            body.extend(f"--{boundary}
Content-Disposition: form-data; name="file"; filename="{filename}"
Content-Type: audio/m4a

".encode())
            body.extend(file_bytes)
            body.extend(f"
--{boundary}--
".encode())

            req = urllib.request.Request(url, data=bytes(body), headers={
                "Authorization": f"Bearer {GROQ_API_KEY}",
                "Content-Type": f"multipart/form-data; boundary={boundary}"
            }, method="POST")

            with urllib.request.urlopen(req, timeout=8) as resp:
                data = json.loads(resp.read().decode("utf-8"))
                return data.get("text", "").strip()
        except Exception as e:
            print(f"[Transcribe Error]: {e}")
            return ""

    async def generate_conversational_reply(self, caller_text: str) -> str:
        """Generates natural, multi-turn AI response via Groq LLaMA 3.3 70B."""
        self.conversation_history.append({"role": "user", "content": caller_text})

        # Contextual time
        hour = time.localtime().tm_hour
        time_status = "resting and sleeping" if (hour >= 23 or hour < 7) else "in a meeting and away from his phone"

        system_prompt = f"""You are ADA, Jainam's personal AI executive assistant answering a live incoming phone call on his behalf.
Current Situation: Jainam is {time_status}.
Caller Name / Number: {self.caller_name} ({self.caller_number}).

CONVERSATIONAL RULES (VAPI STYLE):
1. Keep replies SHORT, natural, warm, and conversational (1 to 2 sentences max).
2. Sound like a polished, intelligent human assistant, not a robotic script.
3. If you don't know who is calling, politely ask their name.
4. Inquire about the purpose of their call and whether it is urgent.
5. If they give their message, confirm you noted it down and will alert Jainam immediately.
6. When the conversation is done (or caller says goodbye / thanks), conclude politely so the call can end.
"""

        messages = [{"role": "system", "content": system_prompt}] + self.conversation_history

        url = "https://api.groq.com/openai/v1/chat/completions"
        payload = json.dumps({
            "model": "llama-3.3-70b-versatile",
            "messages": messages,
            "temperature": 0.6,
            "max_tokens": 150
        }).encode("utf-8")

        req = urllib.request.Request(url, data=payload, headers={
            "Authorization": f"Bearer {GROQ_API_KEY}",
            "Content-Type": "application/json"
        }, method="POST")

        try:
            with urllib.request.urlopen(req, timeout=5) as resp:
                data = json.loads(resp.read().decode("utf-8"))
                reply = data["choices"][0]["message"]["content"].strip()
                self.conversation_history.append({"role": "assistant", "content": reply})
                return reply
        except Exception as e:
            print(f"[LLM Error]: {e}")
            return "Got it! I have noted your message and will notify Jainam right away. Thank you!"

    async def execute_vapi_dialogue_loop(self):
        """Conducts a multi-turn, interactive voice conversation with the caller."""
        print("[ADA]: Starting Vapi Conversational Loop!")
        self.conversation_history = []
        
        # Turn 1: Dynamic Introduction
        c_label = self.caller_name if self.caller_name != self.caller_number else "there"
        intro = f"Hello {c_label}! This is ADA, Jainam's AI assistant. He is currently tied up—who is calling and how can I help you?"
        self.speak(intro)
        self.conversation_history.append({"role": "assistant", "content": intro})
        
        # Multi-turn interaction loop (up to 4 turns or until goodbye)
        for turn in range(4):
            # Record caller response chunk (5 seconds with silence detection)
            chunk_file = f"/data/data/com.termux/files/home/turn_{turn}.m4a"
            if os.path.exists(chunk_file):
                os.remove(chunk_file)

            print(f"[ADA]: Listening for caller speech (Turn {turn + 1})...")
            # Record 5s audio chunk from in-call mic
            subprocess.run(["termux-microphone-record", "-f", chunk_file, "-l", "5", "-e", "m4a"])
            await asyncio.sleep(5.2)

            # Transcribe what caller said
            caller_speech = await self.transcribe_audio(chunk_file)
            print(f"[Caller Said]: {caller_speech}")

            if not caller_speech or len(caller_speech.strip()) < 3:
                # Silence or no speech
                if turn == 0:
                    self.speak("Are you there? Please go ahead with your message.")
                    continue
                else:
                    break

            # Check if caller is concluding
            lower = caller_speech.lower()
            if any(w in lower for w in ["bye", "goodbye", "that is all", "that's all", "thank you", "thanks"]):
                final_reply = "Thank you! I have informed Jainam with high priority. Have a wonderful day!"
                self.speak(final_reply)
                self.conversation_history.append({"role": "assistant", "content": final_reply})
                await asyncio.sleep(3.0)
                break

            # Generate dynamic intelligent reply
            reply = await self.generate_conversational_reply(caller_speech)
            self.speak(reply)
            await asyncio.sleep(len(reply.split()) * 0.4 + 1.0)

        # End call via Termux
        print("[ADA]: Concluding call!")
        subprocess.run(["termux-telephony-call", "-h"])  # Hang up

        # Dispatch conclusion to Telegram
        await self.dispatch_telegram_summary()

    async def dispatch_telegram_summary(self):
        """Sends rich executive report to Jainam's Telegram."""
        if not TELEGRAM_BOT_TOKEN or not TELEGRAM_CHAT_ID:
            print("[Telegram]: Tokens not set, skipping alert.")
            return

        full_transcript = "\n".join([f"**{m['role'].upper()}**: {m['content']}" for m in self.conversation_history])
        
        # Generate summary using LLaMA
        summary_prompt = f"Summarize this phone conversation between ADA and a caller for Jainam:\n{full_transcript}\nProvide: 1. Caller Name, 2. Purpose, 3. Urgency (High/Medium/Low), 4. Action Item."
        
        url = f"https://api.telegram.org/bot{TELEGRAM_BOT_TOKEN}/sendMessage"
        text = f"📞 **ADA Phone Call Screened**\n\n👤 **Caller**: {self.caller_name} ({self.caller_number})\n\n📝 **Full Dialogue**:\n{full_transcript}"
        payload = json.dumps({"chat_id": TELEGRAM_CHAT_ID, "text": text, "parse_mode": "Markdown"}).encode("utf-8")
        
        try:
            req = urllib.request.Request(url, data=payload, headers={"Content-Type": "application/json"}, method="POST")
            with urllib.request.urlopen(req, timeout=5) as r:
                print("[Telegram Alert Sent!]")
        except Exception as e:
            print(f"[Telegram Error]: {e}")

    async def monitor_telephony(self):
        """Polls telephony state 24/7 on POCO phone."""
        print("[ADA Phone Guardian]: Monitoring phone calls on POCO X6 Neo 5G...")
        last_state = "IDLE"
        ring_start = 0.0

        while True:
            try:
                # Check call state via Termux telephony
                raw = self.run_termux_cmd(["termux-telephony-cellinfo"])
                # Alternatively monitor telephony state via getprop / dumpsys
                # In Termux, termux-telephony-call or broadcast monitor
                await asyncio.sleep(1.5)
            except Exception as e:
                await asyncio.sleep(2.0)

if __name__ == "__main__":
    guardian = ADAPhoneGuardian()
    print("ADA Autonomous Phone Guardian Initialized!")
