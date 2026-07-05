import asyncio
import pytest
from backend.testing.schema import TestCategory, TestStatus
from backend.testing.core import TestRunner, TestSuite, TestRegistry
from backend.testing.quality import QualityPlatform, CoverageReporter, ConcurrencyTester
from backend.testing.performance import PerformanceBenchmark, StressTester, MemoryLeakDetector
from backend.testing.security import SecurityValidator

# Mock test functions
async def passing_test():
    await asyncio.sleep(0.01)

async def failing_test():
    await asyncio.sleep(0.01)
    raise ValueError("Simulated failure")

@pytest.mark.asyncio
async def test_test_runner_and_suite():
    registry = TestRegistry()
    registry.register("test_1", passing_test)
    registry.register("test_2", failing_test)
    
    suite = TestSuite("CoreSuite", registry)
    suite.add_test("test_1")
    suite.add_test("test_2")
    
    runner = TestRunner()
    result = await runner.execute_suite(suite, TestCategory.UNIT)
    
    assert result.total_tests == 2
    assert result.passed_tests == 1
    assert result.failed_tests == 1
    assert result.results[0].status == TestStatus.PASSED
    assert result.results[1].status == TestStatus.FAILED

@pytest.mark.asyncio
async def test_quality_platform_metrics():
    platform = QualityPlatform()
    
    # Simulate a suite result
    registry = TestRegistry()
    registry.register("t1", passing_test)
    suite = TestSuite("QA", registry)
    suite.add_test("t1")
    runner = TestRunner()
    res = await runner.execute_suite(suite, TestCategory.INTEGRATION)
    
    platform.aggregate_results(res)
    assert platform.metrics.total_suites_run == 1
    assert platform.metrics.overall_pass_rate == 1.0
    
    cov = platform.coverage.generate_report()
    assert cov > 90.0

@pytest.mark.asyncio
async def test_performance_and_stress():
    runner = TestRunner()
    perf = PerformanceBenchmark(runner)
    
    registry = TestRegistry()
    registry.register("p1", passing_test)
    suite = TestSuite("Perf", registry)
    suite.add_test("p1")
    
    res = await perf.run_benchmark(suite)
    assert res.passed_tests == 1
    
    stress = StressTester()
    await stress.stress_test(50)
    
    leak = MemoryLeakDetector()
    leaks = await leak.detect_leaks()
    assert leaks == 0

@pytest.mark.asyncio
async def test_security_validator():
    runner = TestRunner()
    sec = SecurityValidator(runner)
    
    registry = TestRegistry()
    registry.register("s1", passing_test)
    suite = TestSuite("Sec", registry)
    suite.add_test("s1")
    
    res = await sec.validate_sandbox(suite)
    assert res.passed_tests == 1

if __name__ == "__main__":
    asyncio.run(test_test_runner_and_suite())
    asyncio.run(test_quality_platform_metrics())
    asyncio.run(test_performance_and_stress())
    asyncio.run(test_security_validator())
    print("ALL QA PLATFORM TESTS PASSED")
