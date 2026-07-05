import asyncio
from backend.testing.schema import TestCategory, TestSuiteResult
from backend.testing.core import TestRunner, TestSuite
from backend.core.logger import app_logger

class SecurityValidator:
    def __init__(self, base_runner: TestRunner):
        self.base_runner = base_runner

    async def validate_sandbox(self, suite: TestSuite) -> TestSuiteResult:
        app_logger.info('[SECURITY] Validating sandbox boundaries and permission bypasses...')
        await asyncio.sleep(0.03)
        return await self.base_runner.execute_suite(suite, TestCategory.SECURITY)
