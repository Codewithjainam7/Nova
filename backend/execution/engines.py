import asyncio
from typing import Dict, Any, List, Optional
from datetime import datetime
from backend.execution.schema import ExecutionState, TaskResult, ExecutionProgress
from backend.planner.schema import Task, Plan
from backend.core.logger import app_logger

class ExecutionContext:
    def __init__(self, plan: Plan):
        self.plan = plan
        self.task_states: Dict[str, ExecutionState] = {t.task_id: ExecutionState.PENDING for t in plan.tasks}
        self.task_results: Dict[str, TaskResult] = {}
        self.start_time = datetime.now()
        self.global_context: Dict[str, Any] = {}

class ExecutionQueue:
    def __init__(self, context: ExecutionContext):
        self.context = context
        self.tasks_map = {t.task_id: t for t in context.plan.tasks}
        self.dependencies = context.plan.dependencies
        
    def get_ready_tasks(self) -> List[Task]:
        ready = []
        for task_id, task in self.tasks_map.items():
            if self.context.task_states[task_id] == ExecutionState.PENDING:
                # Check dependencies
                deps = self.dependencies.get(task_id, [])
                if all(self.context.task_states.get(d) == ExecutionState.COMPLETED for d in deps):
                    ready.append(task)
        return ready

    def mark_state(self, task_id: str, state: ExecutionState):
        self.context.task_states[task_id] = state

class RetryEngine:
    def __init__(self, max_retries: int = 3, backoff_factor: float = 2.0):
        self.max_retries = max_retries
        self.backoff_factor = backoff_factor

    async def execute_with_retry(self, task_id: str, func, *args, **kwargs) -> Any:
        retries = 0
        while retries <= self.max_retries:
            try:
                return await func(*args, **kwargs)
            except Exception as e:
                # Mock checking if it's recoverable
                recoverable = True
                if not recoverable or retries == self.max_retries:
                    raise e
                retries += 1
                app_logger.warning(f"Task {task_id} failed. Retrying ({retries}/{self.max_retries})...")
                await asyncio.sleep(self.backoff_factor ** retries)

class TimeoutManager:
    def __init__(self, default_timeout: float = 30.0):
        self.default_timeout = default_timeout

    async def execute_with_timeout(self, task_id: str, timeout: float, func, *args, **kwargs) -> Any:
        app_logger.debug(f"Executing task {task_id} with timeout {timeout}s")
        try:
            return await asyncio.wait_for(func(*args, **kwargs), timeout=timeout)
        except asyncio.TimeoutError:
            app_logger.error(f"Task {task_id} timed out after {timeout}s")
            raise

class CancellationManager:
    def __init__(self):
        self.cancelled = False
        
    def check(self):
        if self.cancelled:
            raise asyncio.CancelledError("Workflow was cancelled.")
            
    def cancel(self):
        self.cancelled = True

class ProgressTracker:
    def __init__(self, context: ExecutionContext):
        self.context = context

    def get_progress(self) -> ExecutionProgress:
        completed = [t for t, s in self.context.task_states.items() if s == ExecutionState.COMPLETED]
        remaining = [t for t, s in self.context.task_states.items() if s in (ExecutionState.PENDING, ExecutionState.READY, ExecutionState.WAITING)]
        running = [t for t, s in self.context.task_states.items() if s == ExecutionState.RUNNING]
        
        return ExecutionProgress(
            current_task_id=running[0] if running else None,
            completed_tasks=completed,
            remaining_tasks=remaining,
            estimated_time_remaining=len(remaining) * 10, # Mock 10s per task
            current_agent="DefaultAgent" if running else None
        )

class ExecutionMetrics:
    def __init__(self):
        self.total_retries = 0
        self.warnings = []
        
    def add_retry(self):
        self.total_retries += 1
        
    def add_warning(self, msg: str):
        self.warnings.append(msg)
