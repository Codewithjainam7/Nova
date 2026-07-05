from typing import Dict, List, Optional
from backend.capabilities.schema import CapabilityDescriptor
from backend.core.logger import app_logger

class CapabilityRegistry:
    def __init__(self):
        # Maps capability_id to a list of versions (sorted or latest last)
        # For simplicity, we just store the latest version in this dictionary
        self._capabilities: Dict[str, CapabilityDescriptor] = {}

    def register_capability(self, capability: CapabilityDescriptor):
        self._capabilities[capability.capability_id] = capability
        app_logger.info(f"Registered capability: {capability.capability_id} v{capability.version}")

    def update_capability(self, capability: CapabilityDescriptor):
        if capability.capability_id in self._capabilities:
            self._capabilities[capability.capability_id] = capability
            app_logger.info(f"Updated capability: {capability.capability_id} v{capability.version}")
        else:
            self.register_capability(capability)

    def remove_capability(self, capability_id: str):
        if capability_id in self._capabilities:
            del self._capabilities[capability_id]
            app_logger.info(f"Removed capability: {capability_id}")

    def get_capability(self, capability_id: str) -> Optional[CapabilityDescriptor]:
        return self._capabilities.get(capability_id)

    def list_capabilities(self) -> List[CapabilityDescriptor]:
        return list(self._capabilities.values())

    def search_capability(self, keyword: str) -> List[CapabilityDescriptor]:
        keyword = keyword.lower()
        results = []
        for cap in self._capabilities.values():
            if keyword in cap.name.lower() or keyword in cap.description.lower() or any(keyword in c.lower() for c in cap.categories):
                results.append(cap)
        return results
