import time
import asyncio
from typing import Any, List, Optional
from backend.settings.schema import SettingsConfiguration, SettingsMetrics, SettingsProfile, SettingItem
from backend.settings.storage import SettingsStore, SettingsSerializer, SettingsBackupManager, SettingsSyncManager
from backend.settings.validation import SettingsValidator, SettingsMigrationManager, SettingsPermissions
from backend.core.logger import app_logger

class SettingsLogger:
    @staticmethod
    def log_change(profile_id: str, key: str, action: str):
        app_logger.info(f"[SETTINGS] Profile {profile_id} -> {action} {key}")

class SettingsManager:
    """Dependency Injection Container for the Settings subsystem."""
    def __init__(self, config: SettingsConfiguration):
        self.config = config
        self.serializer = SettingsSerializer(config)
        self.store = SettingsStore(self.serializer)
        self.backups = SettingsBackupManager()
        self.sync = SettingsSyncManager()
        self.validator = SettingsValidator()
        self.migration = SettingsMigrationManager()
        self.permissions = SettingsPermissions()

class SettingsSystem:
    """Central entrypoint for the NOVA Settings configuration subsystem."""
    def __init__(self):
        self.config = SettingsConfiguration()
        self.metrics = SettingsMetrics()
        self.manager = SettingsManager(self.config)
        self.active_profile: Optional[SettingsProfile] = None

    async def initialize(self, default_profile_id: str = "default"):
        """Loads and migrates the initial profile."""
        profile = await self.manager.store.load_profile(default_profile_id)
        self.active_profile = self.manager.migration.migrate(profile)
        self.metrics.total_profiles = 1

    async def get_setting(self, key: str) -> Any:
        """Retrieves a configuration value from the active profile."""
        if not self.active_profile:
             raise RuntimeError("Settings System not initialized.")
             
        item = self.active_profile.settings.get(key)
        if not item:
            return None
            
        if not self.manager.permissions.can_read(item, "ADMIN"):
             raise PermissionError(f"Cannot read secret setting {key}")
             
        return item.value

    async def update_setting(self, item: SettingItem):
        """Validates and updates a configuration value."""
        start = time.time()
        
        if not self.manager.permissions.can_write(item, "ADMIN"):
             raise PermissionError(f"Cannot write setting {item.key}")
             
        if not self.manager.validator.validate(item):
             raise ValueError(f"Invalid setting value for {item.key}")
             
        self.active_profile.settings[item.key] = item
        await self.manager.store.save_profile(self.active_profile)
        
        SettingsLogger.log_change(self.active_profile.profile_id, item.key, "UPDATED")
        
        elapsed = (time.time() - start) * 1000
        self._update_metric("avg_save_latency_ms", elapsed)

    async def backup_active_profile(self) -> str:
        return await self.manager.backups.create_backup(self.active_profile)

    def _update_metric(self, attr: str, elapsed: float):
        n = getattr(self.metrics, "settings_loaded_count", 1)
        if n > 0:
            current = getattr(self.metrics, attr)
            new_val = ((current * (n - 1)) + elapsed) / n
            setattr(self.metrics, attr, new_val)
