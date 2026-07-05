from enum import Enum
from typing import Dict, List
from backend.core.logger import app_logger

class PermissionType(Enum):
    FILE_SYSTEM = "file_system"
    BROWSER = "browser"
    DESKTOP = "desktop"
    NETWORK = "network"

class PermissionStatus(Enum):
    GRANTED = "granted"
    DENIED = "denied"
    PROMPTED = "prompted"

class PermissionManager:
    """
    Manages permissions and dangerous action detection.
    """
    def __init__(self):
        self._permissions: Dict[PermissionType, PermissionStatus] = {
            PermissionType.FILE_SYSTEM: PermissionStatus.PROMPTED,
            PermissionType.BROWSER: PermissionStatus.PROMPTED,
            PermissionType.DESKTOP: PermissionStatus.PROMPTED,
            PermissionType.NETWORK: PermissionStatus.PROMPTED,
        }

    def request_permission(self, perm_type: PermissionType) -> PermissionStatus:
        """
        Request permission. If prompted, usually would emit an event or ask user.
        For now, defaults to granted for testing unless explicitly denied.
        """
        current = self._permissions.get(perm_type, PermissionStatus.PROMPTED)
        if current == PermissionStatus.PROMPTED:
            # Simulate user granting permission
            app_logger.info(f"Permission {perm_type.value} requested and auto-granted for now.")
            self._permissions[perm_type] = PermissionStatus.GRANTED
            return PermissionStatus.GRANTED
        return current

    def has_permission(self, perm_type: PermissionType) -> bool:
        return self._permissions.get(perm_type) == PermissionStatus.GRANTED

    def is_dangerous_action(self, action: str, target: str) -> bool:
        """Heuristics for dangerous actions (e.g. deleting root dir, formatting disk)"""
        dangerous_keywords = ["rm -rf /", "format", "del /s /q c:\\"]
        combined = f"{action} {target}".lower()
        if any(keyword in combined for keyword in dangerous_keywords):
            app_logger.warning(f"Dangerous action detected: {combined}")
            return True
        return False

permission_manager = PermissionManager()
