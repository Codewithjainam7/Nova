from enum import Enum
from typing import Dict, Any, List, Optional
from pydantic import BaseModel, Field
import uuid
from datetime import datetime

class ResponseType(str, Enum):
    CONVERSATION = "CONVERSATION"
    PLANNING = "PLANNING"
    EXECUTION = "EXECUTION"
    VERIFICATION = "VERIFICATION"
    BROWSER = "BROWSER"
    DESKTOP = "DESKTOP"
    VISION = "VISION"
    EMAIL = "EMAIL"
    SEARCH = "SEARCH"
    MEMORY = "MEMORY"
    WORKFLOW = "WORKFLOW"
    PLUGIN = "PLUGIN"

class ResponseFormat(str, Enum):
    JSON = "JSON"
    MARKDOWN = "MARKDOWN"
    PLAIN_TEXT = "PLAIN_TEXT"

class ResponseInput(BaseModel):
    raw_content: str
    provider: str
    model: str
    response_type: ResponseType
    target_format: ResponseFormat = ResponseFormat.MARKDOWN
    metadata: Dict[str, Any] = {}

class ResponseOutput(BaseModel):
    response_id: str = Field(default_factory=lambda: str(uuid.uuid4()))
    response_type: ResponseType
    provider: str
    model: str
    rendered_content: str
    metadata: Dict[str, Any] = {}
    confidence_score: float = 1.0
    execution_metadata: Dict[str, Any] = {}
    memory_metadata: Dict[str, Any] = {}
    checksum: str
    created_at: datetime = Field(default_factory=datetime.now)

class ResponseMetrics(BaseModel):
    total_responses: int = 0
    total_streamed_chunks: int = 0
    validation_failures: int = 0
    cache_hits: int = 0
    avg_processing_time_ms: float = 0.0
