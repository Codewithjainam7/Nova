from enum import Enum
from typing import Dict, Any, List, Optional
from pydantic import BaseModel, Field
import uuid
from datetime import datetime

class VoiceState(str, Enum):
    IDLE = "IDLE"
    LISTENING = "LISTENING"
    PROCESSING = "PROCESSING"
    SPEAKING = "SPEAKING"
    ERROR = "ERROR"

class AudioFormat(str, Enum):
    PCM_16 = "PCM_16"
    OPUS = "OPUS"
    MP3 = "MP3"
    WAV = "WAV"

class VoiceSession(BaseModel):
    session_id: str = Field(default_factory=lambda: str(uuid.uuid4()))
    state: VoiceState = VoiceState.IDLE
    current_speaker: str = "USER"
    partial_transcript: str = ""
    final_transcript: str = ""
    audio_duration_ms: int = 0
    latency_ms: int = 0
    confidence_score: float = 1.0
    created_at: datetime = Field(default_factory=datetime.now)

class VoiceConfiguration(BaseModel):
    wake_word: str = "ADA"
    sensitivity: float = 0.5
    continuous_listening: bool = False
    stt_provider: str = "whisper"
    tts_provider: str = "cartesia"
    voice_selection: str = "9626c31c-bec5-4cca-baa8-f8ba9e84c8bc"
    speech_speed: float = 1.0
    speech_pitch: float = 1.0
    volume: float = 1.0

class VoiceMetrics(BaseModel):
    total_sessions: int = 0
    wake_word_hits: int = 0
    false_positives: int = 0
    avg_wake_latency_ms: float = 0.0
    avg_stt_latency_ms: float = 0.0
    avg_tts_latency_ms: float = 0.0
