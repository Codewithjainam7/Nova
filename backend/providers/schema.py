from enum import Enum
from typing import Dict, Any, List, AsyncGenerator, Optional
from pydantic import BaseModel, Field

class ProviderType(str, Enum):
    GEMINI = "gemini"
    GROQ = "groq"
    OPENROUTER = "openrouter"
    OLLAMA = "ollama"
    MOCK = "mock"

class Role(str, Enum):
    SYSTEM = "system"
    USER = "user"
    ASSISTANT = "assistant"

class Message(BaseModel):
    role: Role
    content: str

class GenerationRequest(BaseModel):
    messages: List[Message]
    model: str
    temperature: float = 0.7
    max_tokens: int = 1024
    stream: bool = False
    provider_type: Optional[ProviderType] = None # Force specific provider
    timeout: float = 30.0
    retry_count: int = 3

class UsageMetrics(BaseModel):
    prompt_tokens: int = 0
    completion_tokens: int = 0
    total_tokens: int = 0
    estimated_cost: float = 0.0

class GenerationResponse(BaseModel):
    content: str
    usage: UsageMetrics = Field(default_factory=UsageMetrics)
    provider_used: ProviderType
    model_used: str

class StreamingToken(BaseModel):
    token: str
    is_final: bool = False
    usage: Optional[UsageMetrics] = None
    provider_used: Optional[ProviderType] = None
    model_used: Optional[str] = None
