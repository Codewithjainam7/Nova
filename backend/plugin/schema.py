from enum import Enum
from typing import Dict, Any, List, Optional
from pydantic import BaseModel, Field
import uuid
from datetime import datetime

class PluginState(str, Enum):
    UNLOADED = "UNLOADED"
    LOADING = "LOADING"
    LOADED = "LOADED"
    ERROR = "ERROR"
    ENABLED = "ENABLED"
    DISABLED = "DISABLED"

class PluginPermissionType(str, Enum):
    FILESYSTEM = "FILESYSTEM"
    DESKTOP = "DESKTOP"
    BROWSER = "BROWSER"
    VISION = "VISION"
    VOICE = "VOICE"
    SEARCH = "SEARCH"
    EMAIL = "EMAIL"
    MEMORY = "MEMORY"
    CLIPBOARD = "CLIPBOARD"
    NOTIFICATIONS = "NOTIFICATIONS"
    NETWORK = "NETWORK"
    DANGEROUS = "DANGEROUS"

class PluginManifest(BaseModel):
    plugin_id: str
    name: str
    version: str
    author: str
    description: str
    permissions: List[PluginPermissionType] = []
    capabilities: List[str] = []
    dependencies: List[str] = []
    required_runtime_version: str
    required_api_version: str
    homepage: Optional[str] = None
    license: str = "MIT"
    digital_signature: Optional[str] = None

class PluginConfiguration(BaseModel):
    plugin_directory: str = "plugins/"
    strict_sandbox: bool = True
    allow_unsigned: bool = False

class PluginMetrics(BaseModel):
    total_plugins_loaded: int = 0
    total_events_bridged: int = 0
    avg_load_latency_ms: float = 0.0
