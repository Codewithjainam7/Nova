import uuid
from abc import ABC, abstractmethod
from typing import List, Dict, Any
from backend.verification.schema import VerificationContext, VerificationReport, VerificationStatus
from backend.verification.rules import VerificationRule

class VerificationStrategy(ABC):
    """Base class for verification strategies (which run multiple rules)."""
    @property
    @abstractmethod
    def strategy_name(self) -> str:
        pass

    @abstractmethod
    async def execute(self, context: VerificationContext) -> VerificationReport:
        pass

class FilesystemVerification(VerificationStrategy):
    @property
    def strategy_name(self) -> str:
        return "FilesystemVerification"

    async def execute(self, context: VerificationContext) -> VerificationReport:
        # Mock filesystem verification
        expected_file = context.expected_state.get("file_exists")
        if expected_file:
            # Simulate check
            return VerificationReport(
                execution_id=context.execution_id,
                task_id=context.task_id,
                status=VerificationStatus.SUCCESS,
                confidence=1.0,
                evidence={"file_exists": expected_file},
                verification_method=self.strategy_name,
                retry_count=context.retry_count
            )
        return VerificationReport(
            execution_id=context.execution_id,
            task_id=context.task_id,
            status=VerificationStatus.UNKNOWN,
            confidence=0.0,
            verification_method=self.strategy_name,
            retry_count=context.retry_count,
            failure_reason="No expected filesystem state provided"
        )

class ResultVerification(VerificationStrategy):
    @property
    def strategy_name(self) -> str:
        return "ResultVerification"

    async def execute(self, context: VerificationContext) -> VerificationReport:
        # Mock output verification
        if not context.output_data:
            return VerificationReport(
                execution_id=context.execution_id,
                task_id=context.task_id,
                status=VerificationStatus.FAILED,
                confidence=0.9,
                evidence={"output": None},
                verification_method=self.strategy_name,
                retry_count=context.retry_count,
                failure_reason="Tool produced no output",
                recovery_suggestion="Retry execution"
            )
            
        return VerificationReport(
            execution_id=context.execution_id,
            task_id=context.task_id,
            status=VerificationStatus.SUCCESS,
            confidence=0.8,
            evidence={"output": context.output_data},
            verification_method=self.strategy_name,
            retry_count=context.retry_count
        )
