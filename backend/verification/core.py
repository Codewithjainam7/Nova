import asyncio
from typing import List
from backend.verification.schema import VerificationContext, VerificationReport, VerificationStatus
from backend.verification.registry import VerificationRegistry
from backend.verification.pipeline import VerificationPipeline
from backend.core.logger import app_logger

class VerificationMetrics:
    def __init__(self):
        self.total_verifications = 0
        self.failed_verifications = 0
        self.retries_requested = 0

class VerificationLogger:
    @staticmethod
    def log_result(reports: List[VerificationReport]):
        for r in reports:
            app_logger.info(f"Verification {r.verification_id} -> {r.status.value} (Confidence: {r.confidence})")
            if r.status in [VerificationStatus.FAILED, VerificationStatus.RETRY_REQUIRED]:
                app_logger.warning(f"Verification Failure: {r.failure_reason} (Suggestion: {r.recovery_suggestion})")

class VerificationManager:
    """
    Central orchestration for the Verification Engine.
    NEVER plans or executes tasks. ONLY verifies execution success.
    """
    def __init__(self, registry: VerificationRegistry):
        self.registry = registry
        self.pipeline = VerificationPipeline(self.registry)
        self.metrics = VerificationMetrics()

    async def verify_task(self, context: VerificationContext) -> VerificationReport:
        """
        Runs the verification pipeline and aggregates the result.
        Handles recovery rules based on failure types.
        """
        self.metrics.total_verifications += 1
        
        # Prevent infinite loops in retry
        if context.retry_count >= context.max_retries:
            return VerificationReport(
                execution_id=context.execution_id,
                task_id=context.task_id,
                status=VerificationStatus.FAILED,
                confidence=1.0,
                verification_method="MAX_RETRIES",
                retry_count=context.retry_count,
                failure_reason="Max retries exceeded",
                recovery_suggestion="Escalate to user"
            )

        reports = await self.pipeline.run(context)
        VerificationLogger.log_result(reports)
        
        # Aggregate logic: If ANY strategy fails, the entire verification fails.
        overall_status = VerificationStatus.SUCCESS
        lowest_conf = 1.0
        failure_reasons = []
        recovery_suggestions = []
        
        for r in reports:
            lowest_conf = min(lowest_conf, r.confidence)
            
            if r.status == VerificationStatus.FAILED:
                overall_status = VerificationStatus.FAILED
                failure_reasons.append(r.failure_reason)
                if r.recovery_suggestion:
                    recovery_suggestions.append(r.recovery_suggestion)
            elif r.status == VerificationStatus.UNKNOWN and overall_status == VerificationStatus.SUCCESS:
                overall_status = VerificationStatus.UNKNOWN
                
        # Recovery Rules (Recovery Suggestion / Escalate)
        if overall_status == VerificationStatus.FAILED:
            self.metrics.failed_verifications += 1
            if any("Retry" in str(s) for s in recovery_suggestions):
                overall_status = VerificationStatus.RETRY_REQUIRED
                self.metrics.retries_requested += 1
            else:
                overall_status = VerificationStatus.MANUAL_CONFIRMATION
        
        return VerificationReport(
            execution_id=context.execution_id,
            task_id=context.task_id,
            status=overall_status,
            confidence=lowest_conf,
            verification_method="AGGREGATED",
            retry_count=context.retry_count,
            failure_reason=" | ".join(filter(None, failure_reasons)) if failure_reasons else None,
            recovery_suggestion=" | ".join(filter(None, recovery_suggestions)) if recovery_suggestions else None
        )
