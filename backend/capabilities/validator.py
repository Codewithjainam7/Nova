from backend.capabilities.schema import CapabilityResolution
from backend.core.logger import app_logger

class CapabilityValidator:
    @staticmethod
    def validate(resolution: CapabilityResolution) -> bool:
        if not resolution.capability_id or not resolution.capability_name:
            app_logger.error("Invalid resolution: Missing capability ID or name")
            return False
            
        if not resolution.matched_agents and not resolution.fallback_agents:
            app_logger.warning(f"Resolution for {resolution.capability_name} has no matching agents.")
            
        if resolution.confidence_score < 0.0 or resolution.confidence_score > 1.0:
            app_logger.error("Invalid resolution: Confidence score out of bounds")
            return False
            
        return True
