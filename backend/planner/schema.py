from enum import Enum
from typing import List, Optional, Dict, Any
from pydantic import BaseModel, Field

class IntentType(str, Enum):
    LAUNCH_APPLICATION = "Launch Application"
    INTERNET_SEARCH = "Internet Search"
    COMMUNICATION = "Communication"
    DOCUMENT_ANALYSIS = "Document Analysis"
    SYSTEM_MANAGEMENT = "System Management"
    UNKNOWN = "Unknown"

class RiskLevel(str, Enum):
    LOW = "LOW"
    MEDIUM = "MEDIUM"
    HIGH = "HIGH"
    CRITICAL = "CRITICAL"

class Intent(BaseModel):
    primary_intent: IntentType
    confidence: float = Field(..., ge=0.0, le=1.0)
    raw_query: str

class Goal(BaseModel):
    primary_goal: str
    secondary_goals: List[str] = []
    constraints: List[str] = []
    priority: int = 1
    dependencies: List[str] = []
    risk_level: RiskLevel = RiskLevel.LOW

class Task(BaseModel):
    task_id: str
    description: str
    dependencies: List[str] = [] # list of task_ids this task depends on
    is_parallel: bool = False
    required_resources: List[str] = []
    required_agents: List[str] = []
    required_tools: List[str] = []
    risk: RiskLevel = RiskLevel.LOW

class Plan(BaseModel):
    plan_id: str
    intent: Intent
    goal: Goal
    tasks: List[Task]
    dependencies: Dict[str, List[str]] = {} # map of task_id to prerequisite task_ids
    overall_risk: RiskLevel = RiskLevel.LOW
    required_agents: List[str] = []
    required_tools: List[str] = []
    estimated_time_seconds: int = 0
    confirmation_required: bool = False
    clarification_questions: List[str] = []
