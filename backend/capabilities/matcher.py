from typing import List
from backend.capabilities.schema import CapabilityContext, CapabilityDescriptor
from backend.capabilities.registry import CapabilityRegistry
from backend.core.logger import app_logger

class CapabilityMatcher:
    def __init__(self, registry: CapabilityRegistry):
        self.registry = registry

    def find_required_capabilities(self, context: CapabilityContext) -> List[CapabilityDescriptor]:
        """Determine which capabilities are required for a task based on description/context."""
        required = []
        desc_lower = context.task_description.lower()
        
        all_caps = self.registry.list_capabilities()
        for cap in all_caps:
            # Explicit requirement
            if cap.name in context.required_capabilities or cap.capability_id in context.required_capabilities:
                required.append(cap)
                continue
                
            # Heuristic match
            if cap.name.lower() in desc_lower or any(cat in desc_lower for cat in cap.categories):
                required.append(cap)
                
        # Resolve dependencies
        resolved_required = list(required)
        for cap in required:
            for dep_id in cap.dependencies:
                dep_cap = self.registry.get_capability(dep_id)
                if dep_cap and dep_cap not in resolved_required:
                    resolved_required.append(dep_cap)
                    app_logger.debug(f"Added dependency capability: {dep_cap.name}")
                    
        return resolved_required
