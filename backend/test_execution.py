import asyncio
import uuid
import pytest
from datetime import datetime

from backend.planner.schema import Plan, Task, Intent, Goal, IntentType, RiskLevel
from backend.execution.schema import ExecutionState, TaskResult, ExecutionReport
from backend.execution.engines import RetryEngine, TimeoutManager
from backend.execution.core import ExecutionManager, MockTaskExecutor

def create_mock_plan(tasks: list) -> Plan:
    return Plan(
        plan_id=str(uuid.uuid4()),
        intent=Intent(primary_intent=IntentType.UNKNOWN, confidence=1.0, raw_query=""),
        goal=Goal(primary_goal="Test", priority=1),
        tasks=tasks,
        dependencies={}
    )

@pytest.mark.asyncio
async def test_sequential_execution():
    t1 = Task(task_id="t1", description="Task 1")
    t2 = Task(task_id="t2", description="Task 2")
    plan = create_mock_plan([t1, t2])
    plan.dependencies = {"t2": ["t1"]}

    manager = ExecutionManager(MockTaskExecutor(), RetryEngine(max_retries=1), TimeoutManager())
    report = await manager.execute_plan(plan)
    
    assert report.state == ExecutionState.COMPLETED
    assert len(report.task_results) == 2
    assert report.task_results[0].task_id == "t1"
    assert report.task_results[0].state == ExecutionState.COMPLETED
    assert report.task_results[1].task_id == "t2"
    assert report.task_results[1].state == ExecutionState.COMPLETED
    assert len(report.failed_tasks) == 0

@pytest.mark.asyncio
async def test_parallel_execution():
    t1 = Task(task_id="t1", description="Task 1")
    t2 = Task(task_id="t2", description="Task 2")
    plan = create_mock_plan([t1, t2])
    
    manager = ExecutionManager(MockTaskExecutor(), RetryEngine(max_retries=1), TimeoutManager())
    report = await manager.execute_plan(plan)
    
    assert report.state == ExecutionState.COMPLETED
    assert len(report.task_results) == 2

@pytest.mark.asyncio
async def test_retry_and_failure():
    t1 = Task(task_id="t1", description="Will FAIL")
    plan = create_mock_plan([t1])
    
    manager = ExecutionManager(MockTaskExecutor(), RetryEngine(max_retries=2, backoff_factor=1.0), TimeoutManager())
    report = await manager.execute_plan(plan)
    
    assert report.state == ExecutionState.FAILED
    assert report.total_retries == 1  # From metrics point of view
    assert len(report.failed_tasks) == 1
    assert report.verification_required is True

if __name__ == "__main__":
    asyncio.run(test_sequential_execution())
    asyncio.run(test_parallel_execution())
    asyncio.run(test_retry_and_failure())
    print("ALL EXECUTION ENGINE TESTS PASSED")
