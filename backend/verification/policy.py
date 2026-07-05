from typing import List
from backend.verification.schema import VerificationLevel

class VerificationPolicy:
    """Defines which strategies to run based on the VerificationLevel."""
    
    @staticmethod
    def get_required_strategies(level: VerificationLevel) -> List[str]:
        if level == VerificationLevel.NONE:
            return []
        if level == VerificationLevel.BASIC:
            return ["ResultVerification"]
        if level == VerificationLevel.STANDARD:
            return ["ResultVerification", "FilesystemVerification"]
        if level in [VerificationLevel.STRICT, VerificationLevel.CRITICAL]:
            return ["ResultVerification", "FilesystemVerification"] # More in a real app
        return []
