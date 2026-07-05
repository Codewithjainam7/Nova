import asyncio
from datetime import datetime
from typing import List, Optional, Any
from backend.execution.schema import ExecutionState, TaskResult, ExecutionReport, ExecutionProgress
from backend.execution.engines import (
    ExecutionContext, ExecutionQueue, RetryEngine, 
    TimeoutManager, CancellationManager, ProgressTracker, ExecutionMetrics
)
from backend.planner.schema import Plan, Task
from backend.core.logger import app_logger

class TaskExecutorInterface:
    """Interface to abstract away Agent Router / Tools"""
    async def execute_task(self, task: Task) -> Any:
        raise NotImplementedError

class MockTaskExecutor(TaskExecutorInterface):
    """Mock executor for testing Execution Engine."""
    async def execute_task(self, task: Task) -> str:
        app_logger.debug(f"Executing mock task {task.task_id}...")
        await asyncio.sleep(0.1) # Simulate work
        if "FAIL" in task.description:
            raise Exception("Simulated task failure")
        return f"Result of {task.task_id}"

class ExecutionManager:
    """
    Central orchestration for NOVA's Execution Engine.
    Executes the Planner's Output.
    """
    def __init__(
        self,
        task_executor: TaskExecutorInterface,
        retry_engine: RetryEngine,
        timeout_manager: TimeoutManager
    ):
        self.task_executor = task_executor
        self.retry_engine = retry_engine
        self.timeout_manager = timeout_manager

    async def execute_plan(self, plan: Plan) -> ExecutionReport:
        app_logger.info(f"Starting execution for plan {plan.plan_id}")
        context = ExecutionContext(plan)
        queue = ExecutionQueue(context)
        cancellation = CancellationManager()
        progress = ProgressTracker(context)
        metrics = ExecutionMetrics()
        
        # Verify plan
        if not plan.tasks:
            app_logger.warning("Empty plan received")
            return self._build_report(context, metrics, ExecutionState.COMPLETED)
        
        # Main execution loop
        try:
            while True:
                cancellation.check()
                
                ready_tasks = queue.get_ready_tasks()
                if not ready_tasks:
                    # Check if all completed or if there's a deadlock
                    if all(s in (ExecutionState.COMPLETED, ExecutionState.FAILED, ExecutionState.CANCELLED) for s in context.task_states.values()):
                        break
                    
                    running = any(s == ExecutionState.RUNNING for s in context.task_states.values())
                    if not running:
                        metrics.add_warning("Deadlock detected in execution queue")
                        break
                    
                    await asyncio.sleep(0.1)
                    continue

                # For simplicity, sequential execution in this mockup loop, but parallel is supported via asyncio.gather if needed
                # Here we will dispatch all ready tasks concurrently
                tasks_to_run = []
                for task in ready_tasks:
                    queue.mark_state(task.task_id, ExecutionState.RUNNING)
                    tasks_to_run.append(self._execute_task_wrapper(task, context, queue, metrics, cancellation))
                
                if tasks_to_run:
                    await asyncio.gather(*tasks_to_run, return_exceptions=True)

        except asyncio.CancelledError:
            app_logger.warning(f"Plan {plan.plan_id} execution cancelled.")
            for tid, s in context.task_states.items():
                if s in (ExecutionState.PENDING, ExecutionState.READY, ExecutionState.WAITING, ExecutionState.RUNNING):
                    queue.mark_state(tid, ExecutionState.CANCELLED)
                    context.task_results[tid] = TaskResult(task_id=tid, state=ExecutionState.CANCELLED)
            return self._build_report(context, metrics, ExecutionState.CANCELLED)
            
        except Exception as e:
            app_logger.error(f"Execution failed with unexpected error: {e}")
            return self._build_report(context, metrics, ExecutionState.FAILED)

        # Check final state
        final_state = ExecutionState.COMPLETED
        if any(s == ExecutionState.FAILED for s in context.task_states.values()):
            final_state = ExecutionState.FAILED

        return self._build_report(context, metrics, final_state)

    async def _execute_task_wrapper(
        self, 
        task: Task, 
        context: ExecutionContext, 
        queue: ExecutionQueue, 
        metrics: ExecutionMetrics,
        cancellation: CancellationManager
    ):
        start_time = datetime.now()
        task_result = TaskResult(task_id=task.task_id, state=ExecutionState.RUNNING, start_time=start_time)
        try:
            cancellation.check()
            # Wrap execution with retry and timeout
            async def do_execute():
                return await self.task_executor.execute_task(task)
            
            result = await self.retry_engine.execute_with_retry(
                task.task_id, 
                self.timeout_manager.execute_with_timeout,
                task.task_id, 
                30.0, # 30s timeout per task
                do_execute
            )
            
            task_result.state = ExecutionState.COMPLETED
            task_result.result = result
            queue.mark_state(task.task_id, ExecutionState.COMPLETED)
            
        except asyncio.CancelledError:
            task_result.state = ExecutionState.CANCELLED
            task_result.error = "Cancelled"
            queue.mark_state(task.task_id, ExecutionState.CANCELLED)
        except asyncio.TimeoutError:
            task_result.state = ExecutionState.TIMED_OUT
            task_result.error = "Timed out"
            queue.mark_state(task.task_id, ExecutionState.TIMED_OUT)
        except Exception as e:
            task_result.state = ExecutionState.FAILED
            task_result.error = str(e)
            metrics.add_retry() # It failed all retries
            queue.mark_state(task.task_id, ExecutionState.FAILED)
            
        task_result.end_time = datetime.now()
        context.task_results[task.task_id] = task_result

    def _build_report(self, context: ExecutionContext, metrics: ExecutionMetrics, state: ExecutionState) -> ExecutionReport:
        total_time = (datetime.now() - context.start_time).total_seconds()
        failed_tasks = [tid for tid, res in context.task_results.items() if res.state == ExecutionState.FAILED]
        return ExecutionReport(
            plan_id=context.plan.plan_id,
            task_results=list(context.task_results.values()),
            total_execution_time=total_time,
            failed_tasks=failed_tasks,
            total_retries=metrics.total_retries,
            warnings=metrics.warnings,
            verification_required=len(failed_tasks) > 0,
            state=state
        )
