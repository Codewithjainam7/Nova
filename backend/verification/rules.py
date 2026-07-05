from abc import ABC, abstractmethod
from backend.verification.schema import VerificationContext, VerificationReport

class VerificationRule(ABC):
    """Base class for specific verification rules."""
    @property
    @abstractmethod
    def rule_name(self) -> str:
        pass

    @abstractmethod
    async def verify(self, context: VerificationContext) -> VerificationReport:
        """Evaluate the rule and return a verification report."""
        pass
