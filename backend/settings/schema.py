from enum import Enum
from typing import Dict, Any, List, Optional
from pydantic import BaseModel, Field
import uuid
from datetime import datetime

class SettingsCategory(str, Enum):
    GENERAL = "GENERAL"
    APPEARANCE = "APPEARANCE"
    VOICE = "VOICE"
    MEMORY = "MEMORY"
    DESKTOP = "DESKTOP"
    BROWSER = "BROWSER"
    VISION = "VISION"
    SEARCH = "SEARCH"
    EMAIL = "EMAIL"
    PLUGINS = "PLUGINS"
    AI_PROVIDERS = "AI_PROVIDERS"
    SECURITY = "SECURITY"
    PRIVACY = "PRIVACY"
    PERFORMANCE = "PERFORMANCE"
    DEVELOPER = "DEVELOPER"
    ACCESSIBILITY = "ACCESSIBILITY"
    SHORTCUTS = "SHORTCUTS"
    NOTIFICATIONS = "NOTIFICATIONS"
    UPDATES = "UPDATES"

class SettingItem(BaseModel):
    key: str
    category: SettingsCategory
    value: Any
    is_secret: bool = False
    description: Optional[str] = None

class SettingsProfile(BaseModel):
    profile_id: str = Field(default_factory=lambda: str(uuid.uuid4()))
    name: str = "Default"
    version: str = "1.0.0"
    settings: Dict[str, SettingItem] = {}
    last_updated: datetime = Field(default_factory=datetime.now)

class SettingsConfiguration(BaseModel):
    storage_path: str = "data/settings.json"
    backup_path: str = "data/backups/settings/"
    enable_encryption: bool = True

class SettingsMetrics(BaseModel):
    total_profiles: int = 0
    settings_loaded_count: int = 0
    avg_load_latency_ms: float = 0.0
    avg_save_latency_ms: float = 0.0
