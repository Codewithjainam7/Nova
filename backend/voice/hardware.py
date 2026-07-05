import asyncio
import queue
import sounddevice as sd
import numpy as np
import av
import io
from backend.core.logger import app_logger

class AudioRecorder:
    """Abstracts microphone hardware."""
    def __init__(self, sample_rate=16000, channels=1):
        self.is_recording = False
        self.sample_rate = sample_rate
        self.channels = channels
        self.q = queue.Queue()
        self.stream = None

    def _callback(self, indata, frames, time, status):
        if status:
            app_logger.warning(f"AudioRecorder status: {status}")
        self.q.put(bytes(indata))

    async def start(self):
        self.is_recording = True
        # Clear queue
        while not self.q.empty():
            self.q.get_nowait()
            
        self.stream = sd.RawInputStream(
            samplerate=self.sample_rate, 
            blocksize=int(self.sample_rate * 0.1), # 100ms blocks
            channels=self.channels, 
            dtype='int16',
            callback=self._callback
        )
        self.stream.start()
        app_logger.info("Microphone recording started.")

    async def stop(self):
        self.is_recording = False
        if self.stream:
            self.stream.stop()
            self.stream.close()
            self.stream = None
        app_logger.info("Microphone recording stopped.")

    async def read_chunk(self) -> bytes:
        if not self.is_recording:
            return b''
        try:
            # Short yield to event loop if empty
            if self.q.empty():
                await asyncio.sleep(0.01)
            if not self.q.empty():
                return self.q.get_nowait()
        except queue.Empty:
            pass
        return b''

class AudioPlayer:
    """Abstracts speaker hardware."""
    def __init__(self):
        self.is_playing = False

    async def play(self, audio_data: bytes):
        """Plays MP3 audio bytes using PyAV and Sounddevice."""
        self.is_playing = True
        app_logger.info(f"Playing audio: {len(audio_data)} bytes")
        
        def _play_sync():
            try:
                container = av.open(io.BytesIO(audio_data))
                audio_stream = container.streams.audio[0]
                audio_frames = []
                for frame in container.decode(audio_stream):
                    # PyAV frame to numpy array. Shape is (channels, samples). We need (samples, channels)
                    audio_frames.append(frame.to_ndarray().T)
                
                if audio_frames:
                    full_audio = np.concatenate(audio_frames, axis=0)
                    sd.play(full_audio, samplerate=audio_stream.sample_rate)
                    sd.wait()
            except Exception as e:
                app_logger.error(f"Playback failed: {e}")
            finally:
                self.is_playing = False
                
        await asyncio.to_thread(_play_sync)

    async def stop(self):
        sd.stop()
        self.is_playing = False
        app_logger.info("Speaker playback stopped.")
