import asyncio
from typing import AsyncGenerator
from backend.core.logger import app_logger

class SpeechRecognizer:
    """Abstracts STT provider logic (e.g. Whisper)."""
    def __init__(self, provider_name: str):
        self.provider = provider_name

    async def transcribe(self, audio: bytes) -> str:
        # Dummy offline transcription
        app_logger.debug(f"[{self.provider}] Transcribing {len(audio)} bytes of audio.")
        await asyncio.sleep(0.1)
        return "Simulated user transcript."

    async def transcribe_stream(self, audio_stream: AsyncGenerator[bytes, None]) -> AsyncGenerator[str, None]:
        # Dummy streaming transcription
        async for chunk in audio_stream:
            yield "partial... "
            
class SpeechSynthesizer:
    """Abstracts TTS provider logic (e.g. Edge TTS)."""
    def __init__(self, provider_name: str):
        self.provider = provider_name

    async def synthesize(self, text: str) -> bytes:
        # Dummy TTS
        app_logger.debug(f"[{self.provider}] Synthesizing speech for: {text[:20]}...")
        await asyncio.sleep(0.2)
        return b'\x01' * 1024 # Dummy audio bytes

    async def synthesize_stream(self, text: str) -> AsyncGenerator[bytes, None]:
        # Dummy TTS streaming
        words = text.split()
        for word in words:
            await asyncio.sleep(0.05)
            yield b'\x01' * 256
