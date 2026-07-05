import os
import json
from typing import Any, Dict, Optional
from pydantic_settings import BaseSettings, SettingsConfigDict
from pydantic import Field

class AppConfig(BaseSettings):
    """
    Typed configuration manager that loads from .env and environment variables.
    """
    environment: str = Field(default="development", alias="NOVA_ENVIRONMENT")
    debug: bool = Field(default=True, alias="NOVA_DEBUG")
    
    port: int = Field(default=8000, alias="PORT")
    host: str = Field(default="127.0.0.1", alias="HOST")
    
    database_url: str = Field(default="sqlite:///./nova.db", alias="DATABASE_URL")
    
    gemini_api_key: Optional[str] = Field(default=None, alias="GEMINI_API_KEY")
    openai_api_key: Optional[str] = Field(default=None, alias="OPENAI_API_KEY")
    
    playwright_headless: bool = Field(default=True, alias="PLAYWRIGHT_HEADLESS")

    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        extra="ignore"
    )

class FeatureFlags:
    """
    Feature flags manager.
    """
    def __init__(self, flags: Dict[str, bool] = None):
        self._flags = flags or {}

    def is_enabled(self, feature: str, default: bool = False) -> bool:
        return self._flags.get(feature, default)

    def set_flag(self, feature: str, enabled: bool):
        self._flags[feature] = enabled

class ConfigurationManager:
    """
    Manages both application config and runtime configurations/feature flags.
    """
    def __init__(self):
        self.app_config = AppConfig()
        self.feature_flags = FeatureFlags({
            "use_gemini": bool(self.app_config.gemini_api_key),
            "use_openai": bool(self.app_config.openai_api_key),
        })
        self.runtime_config: Dict[str, Any] = {}

    def get_config(self) -> AppConfig:
        return self.app_config

    def reload(self):
        """Hot reload support for .env variables"""
        self.app_config = AppConfig()

    def set_runtime_config(self, key: str, value: Any):
        self.runtime_config[key] = value

    def get_runtime_config(self, key: str, default: Any = None) -> Any:
        return self.runtime_config.get(key, default)

config_manager = ConfigurationManager()
