from enum import Enum
from typing import Dict, Any, List, Optional
from pydantic import BaseModel, Field
import uuid
from datetime import datetime

class MemoryType(str, Enum):
    WORKING_MEMORY = "WORKING_MEMORY"
    CONVERSATION_MEMORY = "CONVERSATION_MEMORY"
    LONG_TERM_MEMORY = "LONG_TERM_MEMORY"
    SEMANTIC_MEMORY = "SEMANTIC_MEMORY"
    EPISODIC_MEMORY = "EPISODIC_MEMORY"
    PROCEDURAL_MEMORY = "PROCEDURAL_MEMORY"
    PREFERENCE_MEMORY = "PREFERENCE_MEMORY"
    TASK_MEMORY = "TASK_MEMORY"
    WORKSPACE_MEMORY = "WORKSPACE_MEMORY"
    TEMPORARY_MEMORY = "TEMPORARY_MEMORY"

class MemoryItem(BaseModel):
    memory_id: str = Field(default_factory=lambda: str(uuid.uuid4()))
    memory_type: MemoryType
    content: str
    metadata: Dict[str, Any] = {}
    embedding: Optional[List[float]] = None
    importance: float = 1.0 # 0.0 to 1.0
    created_at: datetime = Field(default_factory=datetime.now)
    last_accessed_at: datetime = Field(default_factory=datetime.now)
    expires_at: Optional[datetime] = None

class MemoryQuery(BaseModel):
    query_text: str
    memory_types: Optional[List[MemoryType]] = None
    top_k: int = 5
    min_similarity: float = 0.5
    metadata_filter: Dict[str, Any] = {}

class MemoryPolicy(BaseModel):
    max_memory_size_mb: int = 1024
    enable_compression: bool = True
    deduplication_threshold: float = 0.95
    importance_threshold: float = 0.2

class MemoryMetrics(BaseModel):
    total_memories: int = 0
    total_retrievals: int = 0
    cache_hits: int = 0
    storage_size_bytes: int = 0
    avg_retrieval_ms: float = 0.0
