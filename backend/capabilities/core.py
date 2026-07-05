from typing import List, Dict
from backend.capabilities.schema import CapabilityContext, CapabilityResolution
from backend.capabilities.registry import CapabilityRegistry
from backend.capabilities.index import CapabilityIndex
from backend.capabilities.matcher import CapabilityMatcher
from backend.capabilities.scorer import CapabilityScorer
from backend.capabilities.validator import CapabilityValidator
from backend.agents.router.registry import AgentRegistry
from backend.core.logger import app_logger

class CapabilityMetrics:
    def __init__(self):
        self.total_resolutions = 0
        self.failed_resolutions = 0
        self.fallback_used = 0

class CapabilityLogger:
    @staticmethod
    def log_resolution(resolution: CapabilityResolution):
        app_logger.info(f"Resolved Capability {resolution.capability_name} (ID: {resolution.capability_id})")
        app_logger.debug(f"Preferred Agent: {resolution.preferred_agent}, Confidence: {resolution.confidence_score}")
        if resolution.fallback_agents:
            app_logger.debug(f"Fallback Agents: {resolution.fallback_agents}")

class CapabilityResolver:
    """
    Determines WHICH capabilities are required for a task and WHICH registered agents provide them.
    NEVER executes tasks. NEVER chooses tools directly.
    """
    def __init__(self, capability_registry: CapabilityRegistry, agent_registry: AgentRegistry):
        self.capability_registry = capability_registry
        self.agent_registry = agent_registry
        self.index = CapabilityIndex(self.capability_registry)
        self.matcher = CapabilityMatcher(self.capability_registry)
        self.scorer = CapabilityScorer()
        self.metrics = CapabilityMetrics()

    def resolve(self, context: CapabilityContext) -> List[CapabilityResolution]:
        self.metrics.total_resolutions += 1
        
        required_caps = self.matcher.find_required_capabilities(context)
        all_agents = self.agent_registry.get_all_agents()
        
        resolutions = []
        
        for cap in required_caps:
            scored_agents = self.scorer.score_agents(cap, all_agents, context)
            
            preferred_agent = None
            fallback_agents = []
            matched_agents = []
            
            if scored_agents:
                preferred_agent = scored_agents[0][1].agent_id
                fallback_agents = [a.agent_id for s, a in scored_agents[1:]]
                matched_agents = [a.agent_id for s, a in scored_agents]
            else:
                self.metrics.failed_resolutions += 1
                app_logger.warning(f"No agents found for capability {cap.capability_id}")
                
            resolution = CapabilityResolution(
                capability_id=cap.capability_id,
                capability_name=cap.name,
                confidence_score=0.9 if preferred_agent else 0.0,
                matched_agents=matched_agents,
                preferred_agent=preferred_agent,
                fallback_agents=fallback_agents,
                dependencies=cap.dependencies,
                execution_constraints=context.execution_constraints
            )
            
            if CapabilityValidator.validate(resolution):
                resolutions.append(resolution)
                CapabilityLogger.log_resolution(resolution)
            else:
                app_logger.error(f"Resolution validation failed for {cap.capability_id}")
                
        return resolutions
