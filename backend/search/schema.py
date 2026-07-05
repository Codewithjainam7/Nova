from enum import Enum
from typing import Dict, Any, List, Optional
from pydantic import BaseModel, Field
import uuid
from datetime import datetime

class SearchProviderType(str, Enum):
    WEB = "WEB"
    NEWS = "NEWS"
    DOCUMENTATION = "DOCUMENTATION"
    ACADEMIC = "ACADEMIC"
    LOCAL = "LOCAL"

class SearchQuery(BaseModel):
    query_id: str = Field(default_factory=lambda: str(uuid.uuid4()))
    text: str
    providers: List[SearchProviderType] = [SearchProviderType.WEB]
    max_results: int = 5
    metadata: Dict[str, Any] = {}

class SearchResult(BaseModel):
    title: str
    url: str
    snippet: str
    provider: SearchProviderType
    relevance_score: float = 0.0
    authority_score: float = 0.0
    freshness_score: float = 0.0
    final_score: float = 0.0
    timestamp: datetime = Field(default_factory=datetime.now)
    verified: bool = False

class SearchSession(BaseModel):
    session_id: str = Field(default_factory=lambda: str(uuid.uuid4()))
    history: List[SearchQuery] = []
    created_at: datetime = Field(default_factory=datetime.now)

class SearchConfiguration(BaseModel):
    enable_caching: bool = True
    cache_ttl_seconds: int = 3600
    semantic_ranking_weight: float = 0.5
    freshness_ranking_weight: float = 0.3
    authority_ranking_weight: float = 0.2

class SearchMetrics(BaseModel):
    total_queries: int = 0
    cache_hits: int = 0
    failed_queries: int = 0
    avg_search_latency_ms: float = 0.0
    avg_ranking_latency_ms: float = 0.0
    avg_verification_latency_ms: float = 0.0
