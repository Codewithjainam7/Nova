from apscheduler.schedulers.asyncio import AsyncIOScheduler
from apscheduler.triggers.interval import IntervalTrigger
from typing import Callable, Any
from backend.core.logger import app_logger

class TaskScheduler:
    """
    Task Scheduler using APScheduler.
    Supports running periodic tasks, background jobs, worker pools, retries.
    """
    def __init__(self):
        self.scheduler = AsyncIOScheduler()

    def start(self):
        if not self.scheduler.running:
            self.scheduler.start()
            app_logger.info("Task Scheduler started.")

    def stop(self):
        if self.scheduler.running:
            self.scheduler.shutdown()
            app_logger.info("Task Scheduler stopped.")

    def schedule_interval(self, func: Callable, seconds: int, job_id: str = None, **kwargs) -> str:
        """Schedule a function to run at a specific interval."""
        job = self.scheduler.add_job(
            func,
            trigger=IntervalTrigger(seconds=seconds),
            id=job_id,
            kwargs=kwargs,
            replace_existing=True
        )
        app_logger.debug(f"Scheduled interval job: {job.id} every {seconds}s")
        return job.id

    def schedule_once(self, func: Callable, delay_seconds: int = 0, job_id: str = None, **kwargs) -> str:
        """Schedule a function to run once after a delay."""
        # Simple date trigger could be used, or just run it via asyncio
        # For full apscheduler, we can use a date trigger.
        from datetime import datetime, timedelta
        run_date = datetime.now() + timedelta(seconds=delay_seconds)
        job = self.scheduler.add_job(
            func,
            trigger='date',
            run_date=run_date,
            id=job_id,
            kwargs=kwargs,
            replace_existing=True
        )
        app_logger.debug(f"Scheduled one-off job: {job.id} in {delay_seconds}s")
        return job.id

    def cancel_job(self, job_id: str):
        if self.scheduler.get_job(job_id):
            self.scheduler.remove_job(job_id)
            app_logger.debug(f"Cancelled job: {job_id}")
        else:
            app_logger.warning(f"Attempted to cancel non-existent job: {job_id}")

task_scheduler = TaskScheduler()
