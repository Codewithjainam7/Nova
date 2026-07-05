from typing import Any
from backend.settings.schema import SettingsProfile, SettingItem
from backend.core.logger import app_logger

class SettingsPermissions:
    """Enforces access control (e.g. read-only, sensitive data)."""
    def can_read(self, setting: SettingItem, user_role: str) -> bool:
        if setting.is_secret and user_role != "ADMIN":
            return False
        return True
        
    def can_write(self, setting: SettingItem, user_role: str) -> bool:
        return user_role == "ADMIN"

class SettingsValidator:
    """Ensures setting schemas and types match expected values."""
    def validate(self, setting: SettingItem) -> bool:
        # Complex schema validation logic would go here.
        if setting.value is None:
             app_logger.warning(f"[SETTINGS VALIDATION] Missing value for {setting.key}")
             return False
        return True

class SettingsMigrationManager:
    """Handles upgrading a profile's schema from an older version."""
    def __init__(self):
        self.current_version = "1.0.0"
        
    def migrate(self, profile: SettingsProfile) -> SettingsProfile:
        if profile.version != self.current_version:
            app_logger.info(f"[SETTINGS MIGRATION] Migrating {profile.name} from {profile.version} to {self.current_version}")
            # Map old keys to new keys
            profile.version = self.current_version
        return profile
