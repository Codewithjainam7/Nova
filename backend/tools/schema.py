from enum import Enum
from typing import List, Dict, Any, Optional
from pydantic import BaseModel, Field

class ToolCategory(str, Enum):
    DESKTOP = "Desktop"
    BROWSER = "Browser"
    MEMORY = "Memory"
    VOICE = "Voice"
    VISION = "Vision"
    SEARCH = "Search"
    EMAIL = "Email"
    SETTINGS = "Settings"
    FILESYSTEM = "Filesystem"
    CLIPBOARD = "Clipboard"
    WINDOW = "Window"
    CALENDAR = "Calendar"
    REMINDER = "Reminder"
    PLUGIN = "Plugin"
    UTILITY = "Utility"

class ToolHealthStatus(str, Enum):
    HEALTHY = "Healthy"
    DEGRADED = "Degraded"
    OFFLINE = "Offline"

class ToolMetadata(BaseModel):
    version: str
    author: str
    tags: List[str] = []

class ToolDescriptor(BaseModel):
    tool_id: str
    name: str
    description: str
    category: ToolCategory
    metadata: ToolMetadata
    required_capabilities: List[str] = []
    required_permissions: List[str] = []
    input_schema: Dict[str, Any] = {}
    output_schema: Dict[str, Any] = {}
    execution_timeout: float = 30.0
    supports_async: bool = True
    supports_retry: bool = True
    health_status: ToolHealthStatus = ToolHealthStatus.HEALTHY
    dependencies: List[str] = []
