import asyncio
import os
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
            groq_api_key = os.getenv("GROQ_API_KEY", "")
            if groq_api_key:
                try:
                    from groq import Groq
                    import wave, io
                    buf = io.BytesIO()
                    with wave.open(buf, 'wb') as wf:
                        wf.setnchannels(1)
                        wf.setsampwidth(2)
                        wf.setframerate(16000)
                        wf.writeframes(audio)
                    buf.seek(0)
                    g_client = Groq(api_key=groq_api_key)
                    t = g_client.audio.transcriptions.create(
                        file=("audio.wav", buf.read()),
                        model="whisper-large-v3-turbo",
                        response_format="json",
                        language="en",
                        prompt="Ada, WhatsApp, Telegram, Spotify, Jainam"
                    )
                    return t.text.strip()
                except Exception as ge:
                    app_logger.warning(f"Groq STT in SpeechRecognizer failed: {ge}")

            self._ensure_model()
            # Convert raw int16 PCM bytes to float32 numpy array
            audio_array = np.frombuffer(audio, np.int16).astype(np.float32) / 32768.0
            segments, info = self.model.transcribe(audio_array, beam_size=5, initial_prompt="Vedya, WhatsApp, ADA, Jainam")
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
    """Abstracts TTS provider logic using Cartesia."""
    def __init__(self, provider_name: str = "cartesia", voice: str = "9626c31c-bec5-4cca-baa8-f8ba9e84c8bc"):
        self.provider = provider_name
        self.voice = voice
        
        # Load API key directly from environment
        api_key = os.environ.get("CARTESIA_API_KEY", "")
        if not api_key:
            app_logger.warning("CARTESIA_API_KEY is not set. TTS may fail.")
            
        from cartesia import AsyncCartesia
        self.client = AsyncCartesia(api_key=api_key)

    async def synthesize(self, text: str) -> bytes:
        app_logger.debug(f"[{self.provider}] Synthesizing speech for: {text[:20]}...")
        audio_data = b""
        async for chunk in await self.client.tts.sse(
            model_id="sonic-english",
            transcript=text,
            voice_id=self.voice,
            stream=True,
            output_format={
                "container": "raw",
                "encoding": "pcm_f32le",
                "sample_rate": 24000,
            },
        ):
            audio_data += chunk["audio"]
        return audio_data

    async def synthesize_stream(self, text: str):
        async for chunk in await self.client.tts.sse(
            model_id="sonic-english",
            transcript=text,
            voice_id=self.voice,
            stream=True,
            output_format={
                "container": "raw",
                "encoding": "pcm_f32le",
                "sample_rate": 24000,
            },
        ):
            yield chunk["audio"]
