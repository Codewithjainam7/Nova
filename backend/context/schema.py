from enum import Enum
from typing import Dict, Any, List, Optional
from pydantic import BaseModel, Field
import uuid

class ContextType(str, Enum):
    CONVERSATION = "conversation"
    WORKING_MEMORY = "working_memory"
    LONG_TERM_MEMORY = "long_term_memory"
    PLANNER_STATE = "planner_state"
    EXECUTION_STATE = "execution_state"
    VERIFICATION_RESULT = "verification_result"
    DESKTOP_STATE = "desktop_state"
    BROWSER_STATE = "browser_state"
    FILESYSTEM = "filesystem"
    SYSTEM = "system" # time, user preferences

class ContextItem(BaseModel):
    id: str = Field(default_factory=lambda: str(uuid.uuid4()))
    type: ContextType
    content: Any
    relevance_score: float = 1.0 # 0.0 to 1.0
    recency_score: float = 1.0
    importance: float = 1.0
    metadata: Dict[str, Any] = {}
    estimated_tokens: int = 0

class ContextPackage(BaseModel):
    context_id: str = Field(default_factory=lambda: str(uuid.uuid4()))
    conversation_context: List[ContextItem] = []
    memory_context: List[ContextItem] = []
    execution_context: List[ContextItem] = []
    desktop_context: List[ContextItem] = []
    browser_context: List[ContextItem] = []
    search_context: List[ContextItem] = []
    preference_context: List[ContextItem] = []
    metadata: Dict[str, Any] = {}
    total_estimated_tokens: int = 0
    confidence: float = 1.0
