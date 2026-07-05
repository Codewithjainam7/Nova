import time
from typing import Optional, AsyncGenerator
from backend.voice.schema import VoiceSession, VoiceState, VoiceConfiguration, VoiceMetrics
from backend.voice.hardware import AudioRecorder, AudioPlayer
from backend.voice.processors import WakeWordDetector
from backend.voice.pipeline import AudioPipeline, StreamingAudioManager
from backend.voice.providers import SpeechRecognizer, SpeechSynthesizer
from backend.core.logger import app_logger

class VoiceLogger:
    @staticmethod
    def log_session(session: VoiceSession, action: str):
        app_logger.info(f"[VOICE SESSION - {action}] ID: {session.session_id}, State: {session.state}")

class VoiceSessionManager:
    def __init__(self):
        self.active_session: Optional[VoiceSession] = None

    def start_session(self) -> VoiceSession:
        self.active_session = VoiceSession(state=VoiceState.LISTENING)
        VoiceLogger.log_session(self.active_session, "START")
        return self.active_session
        
    def get_session(self) -> Optional[VoiceSession]:
        return self.active_session
        
    def end_session(self):
        if self.active_session:
            self.active_session.state = VoiceState.IDLE
            VoiceLogger.log_session(self.active_session, "END")
            self.active_session = None

class VoiceManager:
    """Internal orchestration of Voice Operations."""
    def __init__(self, config: VoiceConfiguration):
        self.config = config
        self.session_manager = VoiceSessionManager()
        self.recorder = AudioRecorder()
        self.player = AudioPlayer()
        
        self.audio_pipeline = AudioPipeline()
        self.stream_manager = StreamingAudioManager(self.recorder, self.audio_pipeline)
        
        self.wake_word_detector = WakeWordDetector(config.wake_word, config.sensitivity)
        self.stt = SpeechRecognizer(config.stt_provider)
        self.tts = SpeechSynthesizer(config.tts_provider)

class VoiceEngine:
    """Central entrypoint for all voice interactions."""
    def __init__(self):
        self.config = VoiceConfiguration()
        self.metrics = VoiceMetrics()
        self.manager = VoiceManager(self.config)

    async def start_listening(self):
        await self.manager.recorder.start()
        session = self.manager.session_manager.start_session()
        self.metrics.total_sessions += 1

    async def stop_listening(self):
        await self.manager.recorder.stop()
        self.manager.session_manager.end_session()

    async def transcribe_current_stream(self) -> str:
        """Processes the mic stream through STT."""
        session = self.manager.session_manager.get_session()
        if not session:
            raise RuntimeError("No active voice session.")
            
        session.state = VoiceState.PROCESSING
        
        # In a real continuous mode, this would feed to STT stream
        # For prototype, we simulate a single pass
        audio_stream = self.manager.stream_manager.stream_mic()
        
        transcript = ""
        async for partial in self.manager.stt.transcribe_stream(audio_stream):
            session.partial_transcript += partial
            
            # Check wake word
            if self.manager.wake_word_detector.detect(session.partial_transcript):
                app_logger.info("Wake word detected!")
                self.metrics.wake_word_hits += 1
                
        # Final pass mock
        session.final_transcript = "Final simulated transcript after wake word."
        return session.final_transcript

    async def speak(self, text: str, interruptible: bool = True):
        session = self.manager.session_manager.get_session()
        if session:
            session.state = VoiceState.SPEAKING
            
        start = time.time()
        
        audio = await self.manager.tts.synthesize(text)
        await self.manager.player.play(audio)
        
        if session:
            session.state = VoiceState.IDLE
            
        # Metrics update
        elapsed = (time.time() - start) * 1000
        n = self.metrics.total_sessions
        if n > 0:
            self.metrics.avg_tts_latency_ms = ((self.metrics.avg_tts_latency_ms * (n - 1)) + elapsed) / n

    async def stop_speaking(self):
        await self.manager.player.stop()
