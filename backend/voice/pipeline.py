from typing import AsyncGenerator
from backend.voice.processors import NoiseSuppressor, EchoCanceller, VoiceActivityDetector
from backend.voice.audio_buffer import AudioBuffer

class AudioPipeline:
    """Pipelines raw audio through processing steps."""
    def __init__(self):
        self.noise_suppressor = NoiseSuppressor()
        self.echo_canceller = EchoCanceller()
        self.vad = VoiceActivityDetector()

    def process_chunk(self, raw_audio: bytes) -> bytes:
        clean = self.echo_canceller.process(raw_audio)
        clean = self.noise_suppressor.process(clean)
        
        if self.vad.detect(clean):
            return clean
        return b''

class StreamingAudioManager:
    """Manages async streaming of audio data from recorder to STT."""
    def __init__(self, recorder, pipeline: AudioPipeline):
        self.recorder = recorder
        self.pipeline = pipeline
        
    async def stream_mic(self) -> AsyncGenerator[bytes, None]:
        while self.recorder.is_recording:
            chunk = await self.recorder.read_chunk()
            if chunk:
                processed = self.pipeline.process_chunk(chunk)
                if processed:
                    yield processed
            else:
                break
