from enum import Enum
from typing import Dict, Any, List, Optional
from pydantic import BaseModel, Field
import uuid
from datetime import datetime
from backend.context.schema import ContextPackage

class PromptType(str, Enum):
    CONVERSATION = "CONVERSATION"
    PLANNING = "PLANNING"
    EXECUTION = "EXECUTION"
    VERIFICATION = "VERIFICATION"
    MEMORY_RETRIEVAL = "MEMORY_RETRIEVAL"
    MEMORY_UPDATE = "MEMORY_UPDATE"
    BROWSER = "BROWSER"
    DESKTOP = "DESKTOP"
    VISION = "VISION"
    EMAIL = "EMAIL"
    SEARCH = "SEARCH"
    WORKFLOW = "WORKFLOW"
    SYSTEM_PROMPT = "SYSTEM_PROMPT"
    DEVELOPER_PROMPT = "DEVELOPER_PROMPT"
    TOOL_PROMPT = "TOOL_PROMPT"
    PLUGIN_PROMPT = "PLUGIN_PROMPT"

class PromptTemplate(BaseModel):
    template_id: str
    name: str
    version: str
    content: str # The actual prompt template string
    required_variables: List[str] = []

class PromptRequest(BaseModel):
    request_id: str = Field(default_factory=lambda: str(uuid.uuid4()))
    prompt_type: PromptType
    context_package: ContextPackage
    user_input: Optional[str] = None
    variables: Dict[str, Any] = {}
    provider_target: str = "default"

class PromptOutput(BaseModel):
    prompt_id: str = Field(default_factory=lambda: str(uuid.uuid4()))
    prompt_version: str
    prompt_type: PromptType
    rendered_prompt: str
    estimated_tokens: int
    context_sources: List[str] = []
    provider_target: str
    template_used: str
    checksum: str
    created_at: datetime = Field(default_factory=datetime.now)

class PromptMetrics(BaseModel):
    total_prompts_generated: int = 0
    total_tokens_estimated: int = 0
    cache_hits: int = 0
    cache_misses: int = 0
    avg_generation_time_ms: float = 0.0
