import asyncio
from typing import AsyncGenerator
from backend.core.logger import app_logger
from faster_whisper import WhisperModel
import edge_tts
import numpy as np

class SpeechRecognizer:
    """Abstracts STT provider logic using faster-whisper."""
    def __init__(self, provider_name: str = "whisper", model_size: str = "base"):
        self.provider = provider_name
        self.model_size = model_size
        self.model = None

    def _ensure_model(self):
        if self.model is None:
            # Using CPU and int8 for maximum compatibility on the host
            self.model = WhisperModel(self.model_size, device="cpu", compute_type="int8")

    async def transcribe(self, audio: bytes) -> str:
        app_logger.debug(f"[{self.provider}] Transcribing {len(audio)} bytes of audio.")
        if not audio:
            return ""
            
        def _transcribe_sync():
            self._ensure_model()
            # Convert raw int16 PCM bytes to float32 numpy array
            audio_array = np.frombuffer(audio, np.int16).astype(np.float32) / 32768.0
            segments, info = self.model.transcribe(audio_array, beam_size=5)
            text = " ".join([segment.text for segment in segments])
            return text.strip()
            
        return await asyncio.to_thread(_transcribe_sync)

    async def transcribe_stream(self, audio_stream: AsyncGenerator[bytes, None]) -> AsyncGenerator[str, None]:
        buffer = b""
        async for chunk in audio_stream:
            buffer += chunk
            if len(buffer) > 16000 * 2 * 2: # Every ~2 seconds
                partial = await self.transcribe(buffer)
                if partial:
                    yield partial
                buffer = b""
            
class SpeechSynthesizer:
    """Abstracts TTS provider logic using edge-tts."""
    def __init__(self, provider_name: str = "edge-tts", voice: str = "en-US-JennyNeural"):
        self.provider = provider_name
        self.voice = voice

    async def synthesize(self, text: str) -> bytes:
        app_logger.debug(f"[{self.provider}] Synthesizing speech for: {text[:20]}...")
        communicate = edge_tts.Communicate(text, self.voice)
        audio_data = b""
        async for chunk in communicate.stream():
            if chunk["type"] == "audio":
                audio_data += chunk["data"]
        return audio_data

    async def synthesize_stream(self, text: str) -> AsyncGenerator[bytes, None]:
        communicate = edge_tts.Communicate(text, self.voice)
        async for chunk in communicate.stream():
            if chunk["type"] == "audio":
                yield chunk["data"]
