from typing import List, Dict
from backend.capabilities.schema import CapabilityDescriptor
from backend.capabilities.registry import CapabilityRegistry

class CapabilityIndex:
    """Fast lookup index for capabilities."""
    def __init__(self, registry: CapabilityRegistry):
        self.registry = registry
        # A real system would maintain inverse indices, e.g., category -> List[str]

    def get_capabilities_by_category(self, category: str) -> List[CapabilityDescriptor]:
        return [cap for cap in self.registry.list_capabilities() if category in cap.categories]
