import asyncio
from backend.core.logger import app_logger

class NoiseSuppressor:
    def process(self, audio: bytes) -> bytes:
        # Dummy noise suppression
        return audio

class EchoCanceller:
    def process(self, audio: bytes) -> bytes:
        # Dummy AEC
        return audio

class VoiceActivityDetector:
    def detect(self, audio: bytes) -> bool:
        # Dummy VAD - returns true if not empty
        return len(audio) > 0

class WakeWordDetector:
    def __init__(self, wake_word: str, sensitivity: float):
        self.wake_word = wake_word
        self.sensitivity = sensitivity

    def detect(self, transcript_chunk: str) -> bool:
        """Naively checks for wake word in partial transcripts."""
        return self.wake_word.lower() in transcript_chunk.lower()
