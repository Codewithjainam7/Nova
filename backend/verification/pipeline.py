from typing import List
from backend.verification.schema import VerificationContext, VerificationReport, VerificationStatus
from backend.verification.registry import VerificationRegistry
from backend.verification.policy import VerificationPolicy
from backend.core.logger import app_logger

class VerificationPipeline:
    def __init__(self, registry: VerificationRegistry):
        self.registry = registry

    async def run(self, context: VerificationContext) -> List[VerificationReport]:
        required_strategy_names = VerificationPolicy.get_required_strategies(context.level)
        
        if not required_strategy_names:
            app_logger.info(f"Task {context.task_id} requires NO verification (level {context.level.value}).")
            return [VerificationReport(
                execution_id=context.execution_id,
                task_id=context.task_id,
                status=VerificationStatus.SUCCESS,
                confidence=1.0,
                verification_method="NONE",
                retry_count=0
            )]
            
        reports = []
        for name in required_strategy_names:
            strategy = self.registry.get_strategy(name)
            if strategy:
                app_logger.debug(f"Running verification strategy: {name}")
                report = await strategy.execute(context)
                reports.append(report)
            else:
                app_logger.error(f"Required strategy {name} not found in registry!")
                reports.append(VerificationReport(
                    execution_id=context.execution_id,
                    task_id=context.task_id,
                    status=VerificationStatus.UNKNOWN,
                    confidence=0.0,
                    verification_method=name,
                    retry_count=context.retry_count,
                    failure_reason="Strategy not found"
                ))
                
        return reports
