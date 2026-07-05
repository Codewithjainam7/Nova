import asyncio
from backend.core.logger import app_logger

class AudioRecorder:
    """Abstracts microphone hardware."""
    def __init__(self):
        self.is_recording = False

    async def start(self):
        self.is_recording = True
        app_logger.info("Microphone recording started.")

    async def stop(self):
        self.is_recording = False
        app_logger.info("Microphone recording stopped.")

    async def read_chunk(self) -> bytes:
        # Dummy audio data chunk (simulating 100ms of PCM data)
        await asyncio.sleep(0.1)
        return b'\x00' * 1024 if self.is_recording else b''

class AudioPlayer:
    """Abstracts speaker hardware."""
    def __init__(self):
        self.is_playing = False

    async def play(self, audio_data: bytes):
        self.is_playing = True
        app_logger.info(f"Playing audio: {len(audio_data)} bytes")
        # Simulate playback time
        await asyncio.sleep(0.1)
        self.is_playing = False

    async def stop(self):
        self.is_playing = False
        app_logger.info("Speaker playback stopped.")
