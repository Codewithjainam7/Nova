from enum import Enum
from typing import Dict, Any, List, Optional
from pydantic import BaseModel, Field
from datetime import datetime
import uuid

class VerificationLevel(str, Enum):
    NONE = "NONE"
    BASIC = "BASIC"
    STANDARD = "STANDARD"
    STRICT = "STRICT"
    CRITICAL = "CRITICAL"

class VerificationStatus(str, Enum):
    SUCCESS = "SUCCESS"
    FAILED = "FAILED"
    PARTIAL_SUCCESS = "PARTIAL_SUCCESS"
    RETRY_REQUIRED = "RETRY_REQUIRED"
    MANUAL_CONFIRMATION = "MANUAL_CONFIRMATION"
    TIMEOUT = "TIMEOUT"
    UNKNOWN = "UNKNOWN"

class VerificationContext(BaseModel):
    execution_id: str
    task_id: str
    tool_id: str
    level: VerificationLevel = VerificationLevel.STANDARD
    input_data: Dict[str, Any] = {}
    output_data: Dict[str, Any] = {}
    expected_state: Dict[str, Any] = {}
    retry_count: int = 0
    max_retries: int = 3

class VerificationReport(BaseModel):
    verification_id: str = Field(default_factory=lambda: str(uuid.uuid4()))
    execution_id: str
    task_id: str
    status: VerificationStatus
    confidence: float = Field(..., ge=0.0, le=1.0)
    evidence: Dict[str, Any] = {}
    verification_method: str
    retry_count: int
    failure_reason: Optional[str] = None
    recovery_suggestion: Optional[str] = None
    timestamp: datetime = Field(default_factory=datetime.now)
