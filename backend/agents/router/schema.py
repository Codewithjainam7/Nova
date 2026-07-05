from enum import Enum
from typing import List, Dict, Any, Optional
from pydantic import BaseModel, Field

class AgentHealthStatus(str, Enum):
    HEALTHY = "Healthy"
    BUSY = "Busy"
    OFFLINE = "Offline"
    RECOVERING = "Recovering"
    DISABLED = "Disabled"
    UNKNOWN = "Unknown"

class AgentDescriptor(BaseModel):
    agent_id: str
    name: str
    description: str
    supported_tasks: List[str] = []
    capabilities: List[str] = []
    priority: int = 1
    health_status: AgentHealthStatus = AgentHealthStatus.UNKNOWN
    is_available: bool = False

class RoutingContext(BaseModel):
    task_id: str
    task_description: str
    required_resources: List[str] = []
    required_agents: List[str] = []
    required_tools: List[str] = []
    execution_metadata: Dict[str, Any] = {}

class RoutingResult(BaseModel):
    agent_id: str
    agent_name: str
    confidence_score: float = Field(..., ge=0.0, le=1.0)
    reason: str
    fallback_agents: List[str] = []
    health_status: AgentHealthStatus
    required_capabilities: List[str] = []
