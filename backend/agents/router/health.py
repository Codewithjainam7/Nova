from typing import Dict
from backend.agents.router.schema import AgentHealthStatus
from backend.agents.router.registry import AgentRegistry
from backend.core.logger import app_logger

class AgentHealthMonitor:
    def __init__(self, registry: AgentRegistry):
        self.registry = registry

    def update_health(self, agent_id: str, status: AgentHealthStatus):
        agent = self.registry.get_agent(agent_id)
        if agent:
            agent.health_status = status
            app_logger.debug(f"Agent {agent_id} health updated to {status.value}")

    def get_health(self, agent_id: str) -> AgentHealthStatus:
        agent = self.registry.get_agent(agent_id)
        return agent.health_status if agent else AgentHealthStatus.UNKNOWN

class AgentAvailabilityTracker:
    def __init__(self, registry: AgentRegistry):
        self.registry = registry

    def mark_available(self, agent_id: str):
        agent = self.registry.get_agent(agent_id)
        if agent:
            agent.is_available = True
            app_logger.debug(f"Agent {agent_id} marked as available")

    def mark_busy(self, agent_id: str):
        agent = self.registry.get_agent(agent_id)
        if agent:
            agent.is_available = False
            app_logger.debug(f"Agent {agent_id} marked as busy")
            
    def is_available(self, agent_id: str) -> bool:
        agent = self.registry.get_agent(agent_id)
        return agent.is_available if agent else False
