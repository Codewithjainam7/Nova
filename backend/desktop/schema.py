from enum import Enum
from typing import Dict, Any, List, Optional
from pydantic import BaseModel, Field
import uuid
from datetime import datetime

class DesktopActionType(str, Enum):
    MOUSE_MOVE = "MOUSE_MOVE"
    MOUSE_CLICK = "MOUSE_CLICK"
    MOUSE_DRAG = "MOUSE_DRAG"
    MOUSE_SCROLL = "MOUSE_SCROLL"
    KEYBOARD_TYPE = "KEYBOARD_TYPE"
    KEYBOARD_SHORTCUT = "KEYBOARD_SHORTCUT"
    WINDOW_MINIMIZE = "WINDOW_MINIMIZE"
    WINDOW_MAXIMIZE = "WINDOW_MAXIMIZE"
    WINDOW_RESTORE = "WINDOW_RESTORE"
    WINDOW_MOVE = "WINDOW_MOVE"
    WINDOW_RESIZE = "WINDOW_RESIZE"
    WINDOW_FOCUS = "WINDOW_FOCUS"
    APP_LAUNCH = "APP_LAUNCH"
    APP_CLOSE = "APP_CLOSE"
    APP_FIND = "APP_FIND"
    CLIPBOARD_READ = "CLIPBOARD_READ"
    CLIPBOARD_WRITE = "CLIPBOARD_WRITE"
    SCREENSHOT = "SCREENSHOT"
    FS_READ = "FS_READ"
    FS_WRITE = "FS_WRITE"
    FS_COPY = "FS_COPY"
    FS_MOVE = "FS_MOVE"
    FS_DELETE = "FS_DELETE"
    FS_CREATE_DIRECTORY = "FS_CREATE_DIRECTORY"
    FS_CREATE_FILE = "FS_CREATE_FILE"
    FS_RENAME = "FS_RENAME"
    FS_LIST = "FS_LIST"

class DesktopPermissionLevel(str, Enum):
    READ_ONLY = "READ_ONLY"
    AUTOMATION = "AUTOMATION"
    DANGEROUS = "DANGEROUS"

class DesktopAction(BaseModel):
    action_id: str = Field(default_factory=lambda: str(uuid.uuid4()))
    action_type: DesktopActionType
    payload: Dict[str, Any] = {}
    requires_confirmation: bool = False
    timeout_ms: int = 5000

class DesktopSession(BaseModel):
    session_id: str = Field(default_factory=lambda: str(uuid.uuid4()))
    active: bool = True
    permissions: DesktopPermissionLevel = DesktopPermissionLevel.READ_ONLY
    created_at: datetime = Field(default_factory=datetime.now)

class DesktopMetrics(BaseModel):
    total_actions: int = 0
    failed_actions: int = 0
    avg_mouse_latency_ms: float = 0.0
    avg_keyboard_latency_ms: float = 0.0
    avg_screenshot_latency_ms: float = 0.0
