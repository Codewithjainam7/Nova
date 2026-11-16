import asyncio
import os
from typing import AsyncGenerator
from backend.core.logger import app_logger
try:
    from faster_whisper import WhisperModel
except ImportError:
    WhisperModel = None

try:
    import edge_tts
except ImportError:
    edge_tts = None
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
    """
    ADA V2 Studio Neural Voice Synthesizer
    Integrates high-definition neural voice synthesis matching the Ada V2 voice pack (nazirlouis/ada_v2).
    Default: 'en-GB-SoniaNeural' (ADA's signature British studio persona).
    """
    def __init__(self, provider_name: str = "edge_tts", voice: str = "en-GB-SoniaNeural"):
        self.provider = provider_name
        # Allow override via environment variable ADA_VOICE
        self.voice = os.getenv("ADA_VOICE", voice)
        
        # Optional Cartesia fallback if user provides CARTESIA_API_KEY
        self.cartesia_client = None
        api_key = os.environ.get("CARTESIA_API_KEY", "")
        if api_key:
            try:
                from cartesia import AsyncCartesia
                self.cartesia_client = AsyncCartesia(api_key=api_key)
            except ImportError:
                pass

    async def synthesize(self, text: str) -> bytes:
        clean_text = text.replace("*", "").replace("#", "").replace("`", "").strip()
        app_logger.info(f"[SpeechSynthesizer] Synthesizing speech with voice '{self.voice}': {clean_text[:40]}...")
        
        # 1. Primary: High-Definition Edge Neural Voice (ADA V2 Voice Pack)
        try:
            import edge_tts
            communicate = edge_tts.Communicate(clean_text, self.voice)
            audio_chunks = []
            async for chunk in communicate.stream():
                if chunk["type"] == "audio":
                    audio_chunks.append(chunk["data"])
            if audio_chunks:
                return b"".join(audio_chunks)
        except Exception as ee:
            app_logger.warning(f"[SpeechSynthesizer] EdgeTTS notice: {ee}")

        # 2. Fallback: Cartesia if configured
        if self.cartesia_client:
            try:
                audio_data = b""
                async for chunk in await self.cartesia_client.tts.sse(
                    model_id="sonic-english",
                    transcript=clean_text,
                    voice_id=os.getenv("CARTESIA_VOICE_ID", "9626c31c-bec5-4cca-baa8-f8ba9e84c8bc"),
                    stream=True,
                    output_format={"container": "raw", "encoding": "pcm_f32le", "sample_rate": 24000}
                ):
                    audio_data += chunk["audio"]
                return audio_data
            except Exception as ce:
                app_logger.warning(f"[SpeechSynthesizer] Cartesia error: {ce}")

        # Fallback if EdgeTTS fails: return empty bytes (never use robotic system voice)
        return b""

    async def synthesize_stream(self, text: str):
        clean_text = text.replace("*", "").replace("#", "").replace("`", "").strip()
        try:
            import edge_tts
            communicate = edge_tts.Communicate(clean_text, self.voice)
            async for chunk in communicate.stream():
                if chunk["type"] == "audio":
                    yield chunk["data"]
            return
        except Exception as e:
            app_logger.warning(f"[SpeechSynthesizer] Stream fallback notice: {e}")

        # Non-streaming fallback
        full_audio = await self.synthesize(text)
        if full_audio:
            yield full_audio
