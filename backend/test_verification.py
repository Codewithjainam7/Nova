import asyncio
import pytest
from backend.verification.schema import VerificationContext, VerificationLevel, VerificationStatus
from backend.verification.registry import VerificationRegistry
from backend.verification.strategies import ResultVerification, FilesystemVerification
from backend.verification.core import VerificationManager

def setup_manager():
    registry = VerificationRegistry()
    registry.register_strategy(ResultVerification())
    registry.register_strategy(FilesystemVerification())
    return VerificationManager(registry)

@pytest.mark.asyncio
async def test_verification_success():
    manager = setup_manager()
    context = VerificationContext(
        execution_id="e1",
        task_id="t1",
        tool_id="tool1",
        level=VerificationLevel.STANDARD,
        output_data={"result": "ok"},
        expected_state={"file_exists": "/tmp/test.txt"}
    )
    
    report = await manager.verify_task(context)
    assert report.status == VerificationStatus.SUCCESS

@pytest.mark.asyncio
async def test_verification_failure_retry():
    manager = setup_manager()
    # Missing output data should fail ResultVerification and trigger retry suggestion
    context = VerificationContext(
        execution_id="e2",
        task_id="t2",
        tool_id="tool1",
        level=VerificationLevel.BASIC,
        output_data={}, # Empty output
        retry_count=0
    )
    
    report = await manager.verify_task(context)
    assert report.status == VerificationStatus.RETRY_REQUIRED
    assert "Retry" in report.recovery_suggestion

@pytest.mark.asyncio
async def test_verification_max_retries():
    manager = setup_manager()
    context = VerificationContext(
        execution_id="e3",
        task_id="t3",
        tool_id="tool1",
        level=VerificationLevel.BASIC,
        output_data={},
        retry_count=3,
        max_retries=3
    )
    
    report = await manager.verify_task(context)
    # Should skip pipeline and immediately fail due to max retries
    assert report.status == VerificationStatus.FAILED
    assert report.verification_method == "MAX_RETRIES"

@pytest.mark.asyncio
async def test_verification_unknown_strategy():
    # Setup without registering FilesystemVerification
    registry = VerificationRegistry()
    registry.register_strategy(ResultVerification())
    manager = VerificationManager(registry)
    
    context = VerificationContext(
        execution_id="e4",
        task_id="t4",
        tool_id="tool1",
        level=VerificationLevel.STANDARD, # Requires FilesystemVerification
        output_data={"result": "ok"}
    )
    
    report = await manager.verify_task(context)
    # Should have UNKNOWN status because the strategy was missing
    assert report.status == VerificationStatus.UNKNOWN

if __name__ == "__main__":
    asyncio.run(test_verification_success())
    asyncio.run(test_verification_failure_retry())
    asyncio.run(test_verification_max_retries())
    asyncio.run(test_verification_unknown_strategy())
    print("ALL VERIFICATION TESTS PASSED")
