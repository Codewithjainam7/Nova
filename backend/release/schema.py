from enum import Enum
from typing import Dict, Any, List, Optional
from pydantic import BaseModel, Field
import uuid
from datetime import datetime

class BuildType(str, Enum):
    DEVELOPER = "DEVELOPER"
    PRODUCTION = "PRODUCTION"
    DEBUG = "DEBUG"

class ReleasePackageType(str, Enum):
    WINDOWS_INSTALLER = "WINDOWS_INSTALLER"
    PORTABLE = "PORTABLE"
    ZIP = "ZIP"

class SemanticVersion(BaseModel):
    major: int
    minor: int
    patch: int
    build: str
    
    def __str__(self):
        return f"{self.major}.{self.minor}.{self.patch}+{self.build}"

class ReleaseMetrics(BaseModel):
    app_startup_ms: float = 0.0
    memory_usage_mb: float = 0.0
    installer_size_mb: float = 0.0
    update_size_mb: float = 0.0
    total_crashes: int = 0

class TelemetryData(BaseModel):
    session_id: str
    timestamp: datetime = Field(default_factory=datetime.now)
    os_version: str
    app_version: str
    metrics: Dict[str, float] = {}

class CrashReport(BaseModel):
    crash_id: str = Field(default_factory=lambda: str(uuid.uuid4()))
    timestamp: datetime = Field(default_factory=datetime.now)
    stack_trace: str
    subsystem: str
    recovery_successful: bool = False
