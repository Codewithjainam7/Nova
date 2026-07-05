from enum import Enum
from typing import Dict, Any, List, Optional, Tuple
from pydantic import BaseModel, Field
import uuid
from datetime import datetime

class VisionPermissionLevel(str, Enum):
    READ_ONLY = "READ_ONLY"
    DESKTOP_ANALYSIS = "DESKTOP_ANALYSIS"
    BROWSER_ANALYSIS = "BROWSER_ANALYSIS"
    SENSITIVE_REGIONS = "SENSITIVE_REGIONS"

class VisionBoundingBox(BaseModel):
    x: int
    y: int
    width: int
    height: int
    confidence: float
    label: Optional[str] = None
    text_content: Optional[str] = None

class VisionResult(BaseModel):
    result_id: str = Field(default_factory=lambda: str(uuid.uuid4()))
    timestamp: datetime = Field(default_factory=datetime.now)
    full_text: str = ""
    boxes: List[VisionBoundingBox] = []
    metadata: Dict[str, Any] = {}

class VisionSession(BaseModel):
    session_id: str = Field(default_factory=lambda: str(uuid.uuid4()))
    permissions: VisionPermissionLevel = VisionPermissionLevel.DESKTOP_ANALYSIS
    active: bool = True

class VisionMetrics(BaseModel):
    total_images_processed: int = 0
    failed_images: int = 0
    avg_ocr_latency_ms: float = 0.0
    avg_object_detection_latency_ms: float = 0.0
    avg_total_latency_ms: float = 0.0

class VisionConfiguration(BaseModel):
    ocr_provider: str = "tesseract"
    detection_model: str = "yolo_v8_nano"
    confidence_threshold: float = 0.5
