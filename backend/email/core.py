import time
import asyncio
from typing import Any, List, Optional
from datetime import datetime
from backend.email.schema import EmailAction, EmailSession, EmailPermissionLevel, EmailMetrics
from backend.email.adapters import EmailProviderRegistry
from backend.email.workflow import EmailWorkflow, EmailPermissionManager
from backend.core.logger import app_logger

class EmailLogger:
    @staticmethod
    def log_action(action: EmailAction, status: str):
        app_logger.info(f"[EMAIL ACTION - {status}] {action.action_type.name} via {action.provider.name}")

class EmailCache:
    def __init__(self):
        self._cache = {}
        
    def get(self, key: str) -> Optional[Any]:
        return self._cache.get(key)
        
    def set(self, key: str, value: Any):
        self._cache[key] = value

class EmailManager:
    def __init__(self, permission_level: EmailPermissionLevel):
        self.permissions = EmailPermissionManager(permission_level)
        self.registry = EmailProviderRegistry()
        self.workflow = EmailWorkflow()
        self.cache = EmailCache()

class EmailExecutor:
    def __init__(self, manager: EmailManager, metrics: EmailMetrics):
        self.manager = manager
        self.metrics = metrics

    async def execute(self, action: EmailAction) -> Any:
        start = time.time()
        EmailLogger.log_action(action, "START")
        
        if not self.manager.permissions.check(action):
            self.metrics.failed_actions += 1
            raise PermissionError(f"Action {action.action_type.name} denied by permission level {self.manager.permissions.level.name}")
            
        try:
            # Handle AI/Workflow specific actions
            if action.action_type.name == "COMPOSE_AI":
                result = await self.manager.workflow.process_ai_draft(action)
            elif action.action_type.name == "SUMMARIZE_THREAD":
                result = await self.manager.workflow.summarize_thread(action)
            else:
                # Dispatch standard actions to Provider Adapter
                adapter = self.manager.registry.get(action.provider.name)
                if not adapter:
                    raise ValueError(f"No adapter found for provider {action.provider.name}")
                result = await adapter.execute(action)
                
            EmailLogger.log_action(action, "SUCCESS")
            self.metrics.total_actions += 1
            
            elapsed = (time.time() - start) * 1000
            if action.action_type.name == "READ":
                self._update_metric("avg_read_latency_ms", elapsed)
            elif action.action_type.name == "SEND":
                self._update_metric("avg_send_latency_ms", elapsed)
            elif action.action_type.name in ["COMPOSE_AI", "SUMMARIZE_THREAD"]:
                self._update_metric("avg_ai_latency_ms", elapsed)
                
            return result
        except Exception as e:
            EmailLogger.log_action(action, f"FAILED: {str(e)}")
            self.metrics.failed_actions += 1
            raise

    def _update_metric(self, attr: str, elapsed: float):
        n = self.metrics.total_actions
        if n > 0:
            current = getattr(self.metrics, attr)
            new_val = ((current * (n - 1)) + elapsed) / n
            setattr(self.metrics, attr, new_val)

class EmailAgent:
    """Central entrypoint for the Email Agent."""
    def __init__(self, permission_level: EmailPermissionLevel = EmailPermissionLevel.READ_ONLY):
        self.session = EmailSession(permissions=permission_level)
        self.metrics = EmailMetrics()
        self.manager = EmailManager(permission_level)
        self.executor = EmailExecutor(self.manager, self.metrics)

    async def perform_action(self, action: EmailAction) -> Any:
        return await self.executor.execute(action)
