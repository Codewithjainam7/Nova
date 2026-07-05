from typing import List, Dict
from backend.agents.router.schema import RoutingContext, RoutingResult, AgentHealthStatus
from backend.agents.router.registry import AgentRegistry
from backend.agents.router.policy import AgentSelectionPolicy
from backend.agents.router.health import AgentHealthMonitor, AgentAvailabilityTracker
from backend.core.logger import app_logger

class RoutingMetrics:
    def __init__(self):
        self.total_routes = 0
        self.fallback_routes = 0
        self.failed_routes = 0

class RoutingLogger:
    @staticmethod
    def log_decision(result: RoutingResult, context: RoutingContext):
        app_logger.info(f"Routed task {context.task_id} to Agent {result.agent_name} (ID: {result.agent_id})")
        app_logger.debug(f"Reason: {result.reason}, Confidence: {result.confidence_score}")
        if result.fallback_agents:
            app_logger.debug(f"Fallbacks available: {result.fallback_agents}")

class AgentRouter:
    """
    Decides WHICH agent should receive each task from the Execution Engine.
    NEVER plans. NEVER executes tools directly.
    """
    def __init__(
        self,
        registry: AgentRegistry,
        policy: AgentSelectionPolicy,
        health_monitor: AgentHealthMonitor,
        availability_tracker: AgentAvailabilityTracker
    ):
        self.registry = registry
        self.policy = policy
        self.health_monitor = health_monitor
        self.availability_tracker = availability_tracker
        self.metrics = RoutingMetrics()

    def route_task(self, context: RoutingContext) -> RoutingResult:
        self.metrics.total_routes += 1
        
        candidates = self.policy.select_agent(context)
        
        if not candidates:
            self.metrics.failed_routes += 1
            app_logger.error(f"No suitable agent found for task {context.task_id}")
            raise ValueError(f"No suitable agent found for task {context.task_id}")

        primary_agent = candidates[0]
        fallback_agents = [c.agent_id for c in candidates[1:]]

        # Check availability, fallback if busy
        if not primary_agent.is_available and fallback_agents:
            self.metrics.fallback_routes += 1
            # Simple fallback to first available or highest ranked fallback
            for fallback_id in fallback_agents:
                fallback_agent = self.registry.get_agent(fallback_id)
                if fallback_agent and fallback_agent.is_available:
                    primary_agent = fallback_agent
                    fallback_agents.remove(fallback_id)
                    app_logger.info(f"Primary agent busy. Falling back to {primary_agent.name}")
                    break

        result = RoutingResult(
            agent_id=primary_agent.agent_id,
            agent_name=primary_agent.name,
            confidence_score=0.9, # Mock confidence
            reason=f"Matched requirements: {context.required_agents}",
            fallback_agents=fallback_agents,
            health_status=primary_agent.health_status,
            required_capabilities=primary_agent.capabilities
        )

        RoutingLogger.log_decision(result, context)
        return result
