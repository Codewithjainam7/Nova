import asyncio
import time
from typing import List, Callable, Awaitable, Dict
from backend.testing.schema import TestResult, TestCategory, TestStatus, TestSuiteResult
from backend.core.logger import app_logger

class TestLogger:
    @staticmethod
    def log_result(result: TestResult):
        level = app_logger.info if result.status == TestStatus.PASSED else app_logger.error
        level(f"[TEST - {result.category.name}] {result.name} -> {result.status.name} ({result.duration_ms:.2f}ms)")

class TestRegistry:
    """Central registry of all available tests."""
    def __init__(self):
        self.tests: Dict[str, Callable[[], Awaitable[None]]] = {}
        
    def register(self, name: str, func: Callable[[], Awaitable[None]]):
        self.tests[name] = func

class TestSuite:
    """A logical grouping of tests to run."""
    def __init__(self, name: str, registry: TestRegistry):
        self.name = name
        self.registry = registry
        self.selected_tests: List[str] = []
        
    def add_test(self, name: str):
        if name in self.registry.tests:
            self.selected_tests.append(name)
            
    async def run(self, category: TestCategory = TestCategory.UNIT) -> TestSuiteResult:
        suite_result = TestSuiteResult(suite_name=self.name, total_tests=len(self.selected_tests))
        start_time = time.time()
        
        for test_name in self.selected_tests:
            func = self.registry.tests[test_name]
            result = TestResult(test_id=test_name, name=test_name, category=category)
            result.status = TestStatus.RUNNING
            
            test_start = time.time()
            try:
                await func()
                result.status = TestStatus.PASSED
                suite_result.passed_tests += 1
            except Exception as e:
                result.status = TestStatus.FAILED
                result.error_message = str(e)
                suite_result.failed_tests += 1
            finally:
                result.duration_ms = (time.time() - test_start) * 1000
                TestLogger.log_result(result)
                suite_result.results.append(result)
                
        suite_result.total_duration_ms = (time.time() - start_time) * 1000
        return suite_result

class TestRunner:
    """Executes suites and aggregates results."""
    def __init__(self):
        self.registry = TestRegistry()
        
    async def execute_suite(self, suite: TestSuite, category: TestCategory) -> TestSuiteResult:
        return await suite.run(category)
