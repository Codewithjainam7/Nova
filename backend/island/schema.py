from enum import Enum
from typing import Dict, Any, List, Optional
from pydantic import BaseModel, Field
import uuid
from datetime import datetime

class IslandStateType(str, Enum):
    IDLE = "IDLE"
    LISTENING = "LISTENING"
    PROCESSING = "PROCESSING"
    SPEAKING = "SPEAKING"
    EXECUTING = "EXECUTING"
    ERROR = "ERROR"

class IslandAnimationType(str, Enum):
    EXPAND = "EXPAND"
    COLLAPSE = "COLLAPSE"
    MORPH = "MORPH"
    FADE = "FADE"
    SLIDE = "SLIDE"
    PULSE = "PULSE"
    GLOW = "GLOW"
    PROGRESS = "PROGRESS"
    STREAMING = "STREAMING"

class IslandNotificationType(str, Enum):
    SUCCESS = "SUCCESS"
    WARNING = "WARNING"
    ERROR = "ERROR"
    INFO = "INFO"

class IslandEvent(BaseModel):
    event_id: str = Field(default_factory=lambda: str(uuid.uuid4()))
    source: str
    state: IslandStateType
    payload: Dict[str, Any] = {}
    timestamp: datetime = Field(default_factory=datetime.now)

class IslandNotification(BaseModel):
    notification_id: str = Field(default_factory=lambda: str(uuid.uuid4()))
    type: IslandNotificationType
    message: str
    duration_ms: int = 3000

class IslandSession(BaseModel):
    session_id: str = Field(default_factory=lambda: str(uuid.uuid4()))
    active: bool = True
    current_state: IslandStateType = IslandStateType.IDLE

class IslandConfiguration(BaseModel):
    max_notifications: int = 3
    enable_animations: bool = True
    default_animation_ms: int = 300

class IslandMetrics(BaseModel):
    total_events_processed: int = 0
    total_notifications_shown: int = 0
    avg_render_latency_ms: float = 0.0
