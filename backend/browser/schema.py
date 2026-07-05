from enum import Enum
from typing import Dict, Any, List, Optional
from pydantic import BaseModel, Field
import uuid
from datetime import datetime

class BrowserActionType(str, Enum):
    LAUNCH = "LAUNCH"
    CLOSE = "CLOSE"
    NAVIGATE = "NAVIGATE"
    RELOAD = "RELOAD"
    BACK = "BACK"
    FORWARD = "FORWARD"
    NEW_TAB = "NEW_TAB"
    CLOSE_TAB = "CLOSE_TAB"
    SWITCH_TAB = "SWITCH_TAB"
    CLICK = "CLICK"
    DOUBLE_CLICK = "DOUBLE_CLICK"
    RIGHT_CLICK = "RIGHT_CLICK"
    HOVER = "HOVER"
    TYPE = "TYPE"
    FILL = "FILL"
    SELECT = "SELECT"
    CHECK = "CHECK"
    UNCHECK = "UNCHECK"
    SCROLL = "SCROLL"
    EXTRACT_TEXT = "EXTRACT_TEXT"
    EXTRACT_HTML = "EXTRACT_HTML"
    EXTRACT_ATTRIBUTES = "EXTRACT_ATTRIBUTES"
    WAIT_FOR_ELEMENT = "WAIT_FOR_ELEMENT"
    WAIT_FOR_NETWORK = "WAIT_FOR_NETWORK"
    SCREENSHOT = "SCREENSHOT"
    EXPORT_PDF = "EXPORT_PDF"
    DOWNLOAD = "DOWNLOAD"
    UPLOAD = "UPLOAD"
    EXECUTE_JS = "EXECUTE_JS"

class BrowserPermissionLevel(str, Enum):
    READ_ONLY = "READ_ONLY"
    AUTOMATION = "AUTOMATION"
    DOWNLOADS_UPLOADS = "DOWNLOADS_UPLOADS"
    DANGEROUS = "DANGEROUS"

class BrowserAction(BaseModel):
    action_id: str = Field(default_factory=lambda: str(uuid.uuid4()))
    action_type: BrowserActionType
    payload: Dict[str, Any] = {}
    timeout_ms: int = 10000

class BrowserSession(BaseModel):
    session_id: str = Field(default_factory=lambda: str(uuid.uuid4()))
    active: bool = True
    permissions: BrowserPermissionLevel = BrowserPermissionLevel.READ_ONLY
    created_at: datetime = Field(default_factory=datetime.now)

class BrowserMetrics(BaseModel):
    total_actions: int = 0
    failed_actions: int = 0
    avg_navigation_latency_ms: float = 0.0
    avg_dom_lookup_latency_ms: float = 0.0
    avg_screenshot_latency_ms: float = 0.0
