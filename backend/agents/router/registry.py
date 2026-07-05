from typing import Dict, List, Optional
from backend.agents.router.schema import AgentDescriptor, AgentHealthStatus
from backend.core.logger import app_logger

class AgentRegistry:
    def __init__(self):
        self._agents: Dict[str, AgentDescriptor] = {}

    def register(self, agent: AgentDescriptor):
        self._agents[agent.agent_id] = agent
        app_logger.info(f"Registered agent: {agent.agent_id}")

    def get_agent(self, agent_id: str) -> Optional[AgentDescriptor]:
        return self._agents.get(agent_id)

    def get_all_agents(self) -> List[AgentDescriptor]:
        return list(self._agents.values())

    def remove_agent(self, agent_id: str):
        if agent_id in self._agents:
            del self._agents[agent_id]
            app_logger.info(f"Removed agent: {agent_id}")

# Default Agents Constants
DEFAULT_AGENTS = [
    "DesktopAgent",
    "BrowserAgent",
    "MemoryAgent",
    "VoiceAgent",
    "VisionAgent",
    "SearchAgent",
    "EmailAgent",
    "PluginAgent",
    "SettingsAgent",
    "FutureAgentPlaceholder"
]
