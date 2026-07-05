import json
import asyncio
from typing import Dict, Any, List
from backend.settings.schema import SettingsProfile, SettingsConfiguration
from backend.core.logger import app_logger

class SettingsSerializer:
    """Handles parsing and encryption of setting objects."""
    def __init__(self, config: SettingsConfiguration):
        self.config = config
        
    def serialize(self, profile: SettingsProfile) -> str:
        # In a real environment, this would encrypt `is_secret` fields.
        return json.dumps(profile.model_dump(), default=str)
        
    def deserialize(self, data: str) -> SettingsProfile:
        return SettingsProfile(**json.loads(data))

class SettingsBackupManager:
    """Handles snapshot backups of profiles."""
    async def create_backup(self, profile: SettingsProfile) -> str:
        app_logger.info(f"[SETTINGS BACKUP] Backing up profile {profile.name}")
        await asyncio.sleep(0.01) # Simulate IO
        return f"backup_{profile.profile_id}.json"
        
    async def restore_backup(self, backup_id: str) -> SettingsProfile:
        app_logger.info(f"[SETTINGS RESTORE] Restoring {backup_id}")
        await asyncio.sleep(0.01) # Simulate IO
        return SettingsProfile()

class SettingsSyncManager:
    """Handles Cloud Sync (Future Implementation)"""
    async def sync(self, profile: SettingsProfile):
        pass

class SettingsStore:
    """Manages local CRUD operations for profiles."""
    def __init__(self, serializer: SettingsSerializer):
        self.serializer = serializer
        self._profiles: Dict[str, SettingsProfile] = {}
        
    async def save_profile(self, profile: SettingsProfile):
        app_logger.debug(f"[SETTINGS STORE] Saving {profile.name}")
        self._profiles[profile.profile_id] = profile
        await asyncio.sleep(0.01) # Simulate IO
        
    async def load_profile(self, profile_id: str) -> SettingsProfile:
        app_logger.debug(f"[SETTINGS STORE] Loading {profile_id}")
        await asyncio.sleep(0.01) # Simulate IO
        return self._profiles.get(profile_id, SettingsProfile(profile_id=profile_id))
