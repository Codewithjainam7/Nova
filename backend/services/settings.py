import json
import os
from typing import Dict, Any
from backend.core.logger import app_logger

class SettingsService:
    """
    Manages persistent settings for the NOVA application.
    Saves to a JSON file (or database in the future).
    """
    def __init__(self, settings_file: str = "settings.json"):
        self.settings_file = settings_file
        self.settings: Dict[str, Any] = {
            "theme": "dark",
            "voice": "default",
            "ai_provider": "gemini",
            "automation": True,
            "privacy": "strict"
        }
        self.load()

    def load(self):
        if os.path.exists(self.settings_file):
            try:
                with open(self.settings_file, "r") as f:
                    data = json.load(f)
                    self.settings.update(data)
                app_logger.info("Settings loaded successfully.")
            except Exception as e:
                app_logger.error(f"Failed to load settings: {e}")
        else:
            self.save() # Create default settings

    def save(self):
        try:
            with open(self.settings_file, "w") as f:
                json.dump(self.settings, f, indent=4)
            app_logger.debug("Settings saved.")
        except Exception as e:
            app_logger.error(f"Failed to save settings: {e}")

    def get(self, key: str, default: Any = None) -> Any:
        return self.settings.get(key, default)

    def set(self, key: str, value: Any):
        self.settings[key] = value
        self.save()

    def export_settings(self, export_path: str):
        try:
            with open(export_path, "w") as f:
                json.dump(self.settings, f, indent=4)
            app_logger.info(f"Settings exported to {export_path}")
        except Exception as e:
            app_logger.error(f"Failed to export settings: {e}")

    def import_settings(self, import_path: str):
        try:
            with open(import_path, "r") as f:
                data = json.load(f)
                self.settings.update(data)
                self.save()
            app_logger.info(f"Settings imported from {import_path}")
        except Exception as e:
            app_logger.error(f"Failed to import settings: {e}")

settings_service = SettingsService()
