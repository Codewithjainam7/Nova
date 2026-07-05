from typing import List, Dict, Tuple
from backend.capabilities.schema import CapabilityContext, CapabilityDescriptor
from backend.agents.router.schema import AgentDescriptor, AgentHealthStatus

class CapabilityScorer:
    """Calculates match scores for agents based on capability constraints."""
    
    @staticmethod
    def score_agents(capability: CapabilityDescriptor, agents: List[AgentDescriptor], context: CapabilityContext) -> List[Tuple[float, AgentDescriptor]]:
        scored = []
        for agent in agents:
            if agent.health_status not in [AgentHealthStatus.HEALTHY, AgentHealthStatus.BUSY]:
                continue
                
            score = 0.0
            
            # Simple Capability Match
            if capability.name in agent.capabilities or capability.capability_id in agent.capabilities:
                score += 5.0
            
            # Match by categories
            if any(cat in agent.description.lower() for cat in capability.categories):
                score += 2.0
                
            # If agent specifically requires this capability
            if capability.name in context.required_capabilities:
                score += 3.0
                
            # Add priority bonus
            score += float(agent.priority)
            
            # Penalize if busy
            if not agent.is_available:
                score -= 2.0
                
            if score > 0:
                scored.append((score, agent))
                
        # Sort descending by score
        scored.sort(key=lambda x: x[0], reverse=True)
        return scored
