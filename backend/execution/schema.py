from enum import Enum
from typing import List, Dict, Any, Optional
from pydantic import BaseModel
from datetime import datetime

class ExecutionState(str, Enum):
    PENDING = "PENDING"
    READY = "READY"
    RUNNING = "RUNNING"
    WAITING = "WAITING"
    RETRYING = "RETRYING"
    COMPLETED = "COMPLETED"
    CANCELLED = "CANCELLED"
    FAILED = "FAILED"
    TIMED_OUT = "TIMED_OUT"

class TaskResult(BaseModel):
    task_id: str
    state: ExecutionState
    result: Any = None
    error: Optional[str] = None
    retries: int = 0
    start_time: Optional[datetime] = None
    end_time: Optional[datetime] = None

class ExecutionProgress(BaseModel):
    current_task_id: Optional[str] = None
    completed_tasks: List[str] = []
    remaining_tasks: List[str] = []
    estimated_time_remaining: int = 0
    current_agent: Optional[str] = None

class ExecutionReport(BaseModel):
    plan_id: str
    task_results: List[TaskResult]
    total_execution_time: float
    failed_tasks: List[str]
    total_retries: int
    warnings: List[str]
    verification_required: bool = False
    state: ExecutionState = ExecutionState.COMPLETED
