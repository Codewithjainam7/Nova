import asyncio
from backend.testing.schema import TestCategory, TestSuiteResult
from backend.testing.core import TestRunner, TestSuite
from backend.core.logger import app_logger

class IntegrationTestRunner:
    """Specialized runner for complex end-to-end workflows."""
    def __init__(self, base_runner: TestRunner):
        self.base_runner = base_runner
        
    async def run_workflow(self, suite: TestSuite, workflow_name: str) -> TestSuiteResult:
        app_logger.info(f"[INTEGRATION] Starting workflow test: {workflow_name}")
        # In a real scenario, this would orchestrate multiple subsystems
        await asyncio.sleep(0.05)
        return await self.base_runner.execute_suite(suite, TestCategory.INTEGRATION)

class RegressionValidator:
    """Ensures old bugs don't resurface."""
    def __init__(self, base_runner: TestRunner):
        self.base_runner = base_runner
        
    async def validate_previous_bugs(self, suite: TestSuite) -> TestSuiteResult:
        app_logger.info("[REGRESSION] Validating previously fixed bugs...")
        await asyncio.sleep(0.02)
        return await self.base_runner.execute_suite(suite, TestCategory.REGRESSION)
