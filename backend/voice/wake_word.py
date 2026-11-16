"""
ADA Mark VII - Autonomous Wake Word & Real-time Voice Listener Engine
Listens continuously for "Hey ADA" or "ADA" across the operating system.
When triggered with "Hey ADA", verbally responds with "Yes, Boss?" or "Yeah, Boss?"
in ADA's signature Sonia HD studio neural voice, then actively listens for and
executes the user's spoken directive with ultra-fast Groq Whisper transcription.
"""

import os
import re
import time
import io
import math
import struct
import wave
import random
import threading
import winsound
from typing import Optional, Callable
import speech_recognition as sr
from backend.core.logger import app_logger

# Strict wake word regex: requires explicit "Hey Ada" / "Hi Ada" / "Hello Ada" / "OK Ada"
# or the word "Ada" spoken entirely by itself. Never triggers on ambient conversation words.
WAKE_REGEX = re.compile(
    r'(?:\b(?:hey|hi|hello|ok|okay)\s+(?:ada|ayda|aida)\b|^\s*(?:ada|ayda|aida)[\s,.:;!?]*$)',
    re.IGNORECASE
)

# Known Whisper phantom hallucinations on silence / low-volume noise
HALLUCINATION_BLACK_LIST = {
    "thank you", "thank you.", "thank you very much.", "thanks for watching",
    "thanks for watching!", "subtitles by", "subtitle by", "please subscribe",
    "please subscribe.", "bye.", "you", "mbc", "amara.org", "...", "here you go", "here you go."
}

# Pre-rendered natural studio responses in Sonia HD persona
WAKE_RESPONSES = [
    ("yes_boss_1.wav", "Yes, Boss?"),
    ("yes_boss_2.wav", "Yeah, Boss?"),
    ("yes_boss_1.wav", "Yes, Boss?"),
    ("yes_boss_2.wav", "Yeah, Boss?"),
    ("yes_boss_3.wav", "At your service, Boss."),
    ("yes_boss_4.wav", "I'm here, Boss."),
    ("yes_boss_5.wav", "Listening, Boss.")
]

def calculate_rms(raw_pcm: bytes) -> float:
    """Calculates root-mean-square audio energy of 16-bit PCM buffer in <2ms."""
    if not raw_pcm:
        return 0.0
    count = len(raw_pcm) // 2
    if count == 0:
        return 0.0
    shorts = struct.unpack(f"<{count}h", raw_pcm[:count * 2])
    sum_sq = sum(s * s for s in shorts)
    return math.sqrt(sum_sq / count)

class WakeWordService:
    def __init__(
        self,
        on_wake_detected: Optional[Callable[[str, str, str], None]] = None,
        on_listening_state: Optional[Callable[[str], None]] = None,
        on_directive_ready: Optional[Callable[[str], None]] = None
    ):
        self.on_wake_detected = on_wake_detected
        self.on_listening_state = on_listening_state
        self.on_directive_ready = on_directive_ready
        
        self.recognizer = sr.Recognizer()
        self.recognizer.dynamic_energy_threshold = True
        self.recognizer.pause_threshold = 0.8
        self.recognizer.phrase_threshold = 0.3
        self.recognizer.non_speaking_duration = 0.5
        
        self.microphone: Optional[sr.Microphone] = None
        self._thread: Optional[threading.Thread] = None
        self._stop_event = threading.Event()
        self.is_running = False
        self.is_speaking = False  # Suppress listening while ADA speaks
        self.groq_api_key = os.getenv("GROQ_API_KEY", "")

        # Sound directory paths
        base_dir = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
        self.wake_sound_dir = os.path.join(base_dir, "backend", "voice", "wake_responses")

    def play_oral_acknowledgement(self) -> str:
        """Plays a pre-rendered Sonia HD verbal greeting ('Yes, Boss?' / 'Yeah, Boss?')."""
        choice_file, text = random.choice(WAKE_RESPONSES)
        wav_path = os.path.join(self.wake_sound_dir, choice_file)
        app_logger.info(f"[WakeWord] Playing verbal response: '{text}' ({choice_file})")
        
        try:
            if os.path.exists(wav_path):
                # Play synchronously on the background daemon thread
                winsound.PlaySound(wav_path, winsound.SND_FILENAME)
            else:
                app_logger.warning(f"[WakeWord] Wav not found: {wav_path}")
        except Exception as e:
            app_logger.error(f"[WakeWord] Audio playback error: {e}")
            
        return text

    def set_speaking(self, speaking: bool):
        """Pauses listener while ADA speaks to prevent acoustic self-triggering."""
        self.is_speaking = speaking
        app_logger.debug(f"[WakeWord] Speaking state set to: {speaking}")

    def _transcribe_audio(self, audio_data: sr.AudioData) -> str:
        """Transcribes audio using Groq Whisper (~150ms) or Google Speech fallback."""
        raw_pcm = audio_data.get_raw_data()
        rms = calculate_rms(raw_pcm)
        app_logger.debug(f"[WakeWord] Captured audio chunk RMS: {rms:.1f}")
        if rms < 220:
            # Ambient room murmur, distant speech, fan noise - ignore completely
            return ""

        wav_bytes = audio_data.get_wav_data(convert_rate=16000, convert_width=2)
        
        # 1. Groq Whisper Turbo (~150ms, world-class precision)
        if self.groq_api_key:
            try:
                from groq import Groq
                client = Groq(api_key=self.groq_api_key)
                res = client.audio.transcriptions.create(
                    file=("audio.wav", wav_bytes),
                    model="whisper-large-v3-turbo",
                    response_format="json",
                    language="en",
                    prompt=None  # Never pass sentences in prompt to prevent Whisper echo hallucinations
                )
                text = (res.text or "").strip()
                # Filter out known Whisper silence hallucinations
                if text.lower().rstrip(".!?,") in HALLUCINATION_BLACK_LIST or len(text) < 3:
                    return ""
                if text:
                    return text
            except Exception as e:
                app_logger.warning(f"[WakeWord] Groq Whisper error: {e}. Falling back to Google Speech.")

        # 2. Fallback: Free Google Speech Recognizer
        try:
            text = self.recognizer.recognize_google(audio_data)
            return (text or "").strip()
        except Exception:
            return ""

    def _listen_loop(self):
        """Continuous background thread listening to default OS microphone."""
        app_logger.info("[WakeWord] Background microphone listener thread started.")
        
        try:
            self.microphone = sr.Microphone()
            with self.microphone as source:
                app_logger.info("[WakeWord] Calibrating microphone for ambient room acoustics...")
                self.recognizer.adjust_for_ambient_noise(source, duration=0.8)
                if self.recognizer.energy_threshold < 350:
                    self.recognizer.energy_threshold = 350
                app_logger.info(f"[WakeWord] Calibrated. Baseline energy threshold: {self.recognizer.energy_threshold:.1f}")
        except Exception as e:
            app_logger.error(f"[WakeWord] Failed to initialize microphone: {e}")
            self.is_running = False
            return

        while not self._stop_event.is_set():
            # If ADA is speaking, sleep briefly to avoid listening to own TTS output
            if self.is_speaking:
                time.sleep(0.15)
                continue

            try:
                with self.microphone as source:
                    audio = self.recognizer.listen(
                        source,
                        timeout=1.0,
                        phrase_time_limit=8.0
                    )
            except sr.WaitTimeoutError:
                continue
            except Exception as e:
                app_logger.debug(f"[WakeWord] Listen capture error: {e}")
                time.sleep(0.1)
                continue

            if self.is_speaking:
                continue

            # Transcribe phrase
            transcript = self._transcribe_audio(audio)
            if not transcript:
                continue

            app_logger.info(f"[WakeWord] Heard speech: '{transcript}'")

            # Check for "Hey ADA" or "ADA"
            match = WAKE_REGEX.search(transcript)
            if match:
                wake_phrase = match.group(0).strip()
                directive = transcript[match.end():].strip().lstrip(",.-: ")
                app_logger.info(f"[WakeWord] *** WAKE WORD DETECTED: '{wake_phrase}' | Tail Directive: '{directive}' ***")
                
                # Filter directive: If it's in hallucination black list or empty, ignore tail
                if directive.lower().rstrip(".!?,") in HALLUCINATION_BLACK_LIST:
                    directive = ""

                self._respond_and_listen_for_directive(wake_phrase, direct_command=directive)

        app_logger.info("[WakeWord] Background microphone listener thread stopped.")

    def _respond_and_listen_for_directive(self, wake_phrase: str, direct_command: str = ""):
        """Verbally acknowledges in Sonia HD, expands UI, then executes or listens for command."""
        self.set_speaking(True)
        
        # Pick response text
        choice_file, oral_text = random.choice(WAKE_RESPONSES)
        wav_path = os.path.join(self.wake_sound_dir, choice_file)
        
        # 1. Notify frontend UI to expand into active listening mode
        if self.on_wake_detected:
            try:
                self.on_wake_detected(wake_phrase, direct_command, oral_text)
            except Exception as ex:
                app_logger.error(f"[WakeWord] Callback error: {ex}")

        # 2. Speak "Yes, Boss?" synchronously
        try:
            if os.path.exists(wav_path):
                winsound.PlaySound(wav_path, winsound.SND_FILENAME)
        except Exception as e:
            app_logger.error(f"[WakeWord] Audio playback error: {e}")

        # Brief delay to let audio buffer finish playing before mic opens
        time.sleep(0.18)
        self.set_speaking(False)

        # If user spoke a REAL directive directly in one breath (e.g. "Hey Ada lock my laptop")
        direct_clean = WAKE_REGEX.sub('', direct_command).strip().strip(",.-: ")
        if direct_clean and len(direct_clean.split()) >= 2 and direct_clean.lower() not in ["ada", "hey ada", "ai assistant", "ada is an ai assistant."]:
            app_logger.info(f"[WakeWord] Direct command dispatched immediately: '{direct_clean}'")
            if self.on_directive_ready:
                self.on_directive_ready(direct_clean)
            return

        # Otherwise, user just said "Hey Ada" -> update UI to "Listening to you, Boss..." and listen!
        if self.on_listening_state:
            try:
                self.on_listening_state("Listening to you, Boss...")
            except Exception as ex:
                app_logger.error(f"[WakeWord] Callback error: {ex}")

        # 4. Now listen for the user's spoken command!
        self._listen_for_followup()

    def _listen_for_followup(self):
        """Actively waits and listens for user's command after wake word is spoken."""
        app_logger.info("[WakeWord] Awaiting spoken command from user...")
        if not self.microphone:
            return

        try:
            with self.microphone as source:
                # Active listening window: up to 6.5s timeout, up to 12s speech
                followup_audio = self.recognizer.listen(
                    source,
                    timeout=6.5,
                    phrase_time_limit=12.0
                )
                
            followup_text = self._transcribe_audio(followup_audio)
            if followup_text:
                # Clean any accidental repetition of wake phrase
                clean_directive = WAKE_REGEX.sub('', followup_text).strip().strip(",.-: ")
                if not clean_directive or clean_directive.lower() in ["hey ada", "ada", "hey", "hello", "hi"]:
                    app_logger.info(f"[WakeWord] Follow-up ignored as pure wake repetition: '{followup_text}'")
                    return

                if len(clean_directive) > 2 and clean_directive.lower() not in HALLUCINATION_BLACK_LIST:
                    app_logger.info(f"[WakeWord] Follow-up directive heard: '{clean_directive}'")
                    if self.on_directive_ready:
                        self.on_directive_ready(clean_directive)
                else:
                    app_logger.info(f"[WakeWord] Follow-up disregarded as non-directive: '{clean_directive}'")
        except sr.WaitTimeoutError:
            app_logger.info("[WakeWord] Follow-up timed out without speech.")
            if self.on_listening_state:
                try:
                    self.on_listening_state("idle")
                except Exception:
                    pass
        except Exception as e:
            app_logger.debug(f"[WakeWord] Follow-up capture error: {e}")

    def start(self):
        """Starts the background wake word listener."""
        if self.is_running:
            return
        self._stop_event.clear()
        self.is_running = True
        self._thread = threading.Thread(target=self._listen_loop, daemon=True, name="AdaWakeWordDaemon")
        self._thread.start()
        app_logger.info("[WakeWord] Service started.")

    def stop(self):
        """Stops the background wake word listener."""
        if not self.is_running:
            return
        self._stop_event.set()
        self.is_running = False
        if self._thread:
            self._thread.join(timeout=2.0)
            self._thread = None
        app_logger.info("[WakeWord] Service stopped.")

    def status(self) -> dict:
        return {
            "running": self.is_running,
            "speaking": self.is_speaking,
            "energy_threshold": getattr(self.recognizer, "energy_threshold", 0)
        }
