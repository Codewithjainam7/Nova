from pydantic import BaseModel, Field
from typing import List, Dict, Any, Optional
from datetime import datetime

class CapabilityDescriptor(BaseModel):
    capability_id: str
    name: str
    version: str = "1.0.0"
    description: str
    categories: List[str] = []
    metadata: Dict[str, Any] = {}
    dependencies: List[str] = []
    registered_at: datetime = Field(default_factory=datetime.now)

class CapabilityContext(BaseModel):
    task_id: str
    task_description: str
    required_capabilities: List[str] = []
    execution_constraints: Dict[str, Any] = {}
    
class CapabilityResolution(BaseModel):
    capability_id: str
    capability_name: str
    confidence_score: float = Field(..., ge=0.0, le=1.0)
    matched_agents: List[str] = []
    preferred_agent: Optional[str] = None
    fallback_agents: List[str] = []
    dependencies: List[str] = []
    execution_constraints: Dict[str, Any] = {}
