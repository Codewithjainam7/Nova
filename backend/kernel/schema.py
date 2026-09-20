from enum import Enum
from typing import Dict, Any, List, Optional
from pydantic import BaseModel, Field
import uuid
from datetime import datetime

class KernelState(str, Enum):
    BOOTING = "BOOTING"
    INITIALIZING = "INITIALIZING"
    IDLE = "IDLE"
    PLANNING = "PLANNING"
    EXECUTING = "EXECUTING"
    WAITING = "WAITING"
    STREAMING = "STREAMING"
    COMPLETED = "COMPLETED"
    RECOVERING = "RECOVERING"
    ERROR = "ERROR"
    SHUTDOWN = "SHUTDOWN"

class KernelConfiguration(BaseModel):
    max_concurrent_sessions: int = 10
    timeout_seconds: float = 300.0
    enable_telemetry: bool = True
    recovery_retries: int = 3

class KernelContext(BaseModel):
    session_id: str
    metadata: Dict[str, Any] = {}
    history: List[Any] = []

class KernelRequest(BaseModel):
    request_id: str = Field(default_factory=lambda: str(uuid.uuid4()))
    conversation_id: str = "default"
    user_input: str
    metadata: Dict[str, Any] = {}
    timeout: Optional[float] = None

class KernelResponse(BaseModel):
    request_id: str
    session_id: str
    status: KernelState
    content: str
    metrics: Dict[str, Any] = {}
    error: Optional[str] = None
    created_at: datetime = Field(default_factory=datetime.now)

class KernelMetrics(BaseModel):
    total_requests: int = 0
    successful_requests: int = 0
    failed_requests: int = 0
    avg_latency_ms: float = 0.0
    active_sessions: int = 0
