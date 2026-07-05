from typing import List, Optional
from backend.agents.router.schema import AgentDescriptor, RoutingContext, AgentHealthStatus
from backend.agents.router.registry import AgentRegistry
from backend.core.logger import app_logger

class AgentSelectionPolicy:
    def __init__(self, registry: AgentRegistry):
        self.registry = registry

    def select_agent(self, context: RoutingContext) -> List[AgentDescriptor]:
        """
        Returns a sorted list of suitable agents (primary first, then fallbacks).
        """
        all_agents = self.registry.get_all_agents()
        candidates = []

        for agent in all_agents:
            # Never choose an unhealthy agent
            if agent.health_status not in [AgentHealthStatus.HEALTHY, AgentHealthStatus.BUSY]:
                continue
            
            # Simple Capability Matcher (Heuristic for now)
            # In a real system, the Capability Resolver handles complex matching
            score = 0
            if any(req.lower() in agent.name.lower() or req.lower() in [s.lower() for s in agent.supported_tasks] for req in context.required_agents):
                score += 10
                
            if any(req.lower() in agent.name.lower() for req in context.required_tools):
                score += 5
                
            # If we requested specific agents and this isn't one of them, and score is 0, skip
            if context.required_agents and score == 0:
                continue

            candidates.append((score, agent))

        # Sort by score (descending), priority (descending), availability (True first)
        candidates.sort(key=lambda x: (x[0], x[1].priority, x[1].is_available), reverse=True)
        
        sorted_agents = [agent for score, agent in candidates]
        app_logger.debug(f"Selection policy yielded {len(sorted_agents)} candidates for task {context.task_id}")
        return sorted_agents
