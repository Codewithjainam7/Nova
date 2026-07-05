from typing import List
from backend.memory.schema import MemoryQuery, MemoryItem
from backend.memory.store import MemoryStore, MemoryCache
from backend.memory.embedder import MemoryEmbedder
from backend.memory.ranker import MemoryRanker
from backend.core.logger import app_logger
from datetime import datetime

class MemoryRetriever:
    """Handles querying and ranking memories."""
    def __init__(self, store: MemoryStore, cache: MemoryCache, embedder: MemoryEmbedder, ranker: MemoryRanker):
        self.store = store
        self.cache = cache
        self.embedder = embedder
        self.ranker = ranker

    async def retrieve(self, query: MemoryQuery) -> List[MemoryItem]:
        app_logger.info(f"Retrieving memory for query: {query.query_text}")
        
        # 1. Embed query
        query_embedding = await self.embedder.embed(query.query_text)
        
        # 2. Vector Search
        results = await self.store.search(query, query_embedding)
        
        if not results:
            return []
            
        # 3. Update access times
        now = datetime.now()
        for item in results:
            item.last_accessed_at = now
            await self.store.update(item)
            
        # 4. Rank
        # For prototype, assume search returns a perfect match score array (mocked 1.0s)
        base_scores = [1.0] * len(results) 
        ranked = self.ranker.rank(results, base_scores)
        
        # 5. Top K
        return ranked[:query.top_k]
