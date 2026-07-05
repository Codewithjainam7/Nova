from typing import List, Dict, Optional
from backend.memory.schema import MemoryItem, MemoryQuery
from backend.core.logger import app_logger

class MemoryCache:
    """In-memory cache for fast memory retrieval."""
    def __init__(self):
        self._cache: Dict[str, MemoryItem] = {}

    def get(self, memory_id: str) -> Optional[MemoryItem]:
        return self._cache.get(memory_id)

    def set(self, item: MemoryItem):
        self._cache[item.memory_id] = item

    def delete(self, memory_id: str):
        if memory_id in self._cache:
            del self._cache[memory_id]

class MemoryStore:
    """Abstraction for the Vector Database (e.g. ChromaDB)."""
    def __init__(self):
        # We mock a vector DB with a simple dict for this prototype
        self._db: Dict[str, MemoryItem] = {}

    async def add(self, item: MemoryItem):
        self._db[item.memory_id] = item
        
    async def get(self, memory_id: str) -> Optional[MemoryItem]:
        return self._db.get(memory_id)

    async def update(self, item: MemoryItem):
        if item.memory_id in self._db:
            self._db[item.memory_id] = item

    async def delete(self, memory_id: str):
        if memory_id in self._db:
            del self._db[memory_id]

    async def search(self, query: MemoryQuery, query_embedding: List[float]) -> List[MemoryItem]:
        """Naive simulated vector search."""
        results = []
        for item in self._db.values():
            if query.memory_types and item.memory_type not in query.memory_types:
                continue
            
            # Simulated similarity check. 
            # In a real app this uses cosine similarity on item.embedding and query_embedding
            # We mock the similarity score via exact match or just returning it for testing
            
            similarity = 1.0 if query.query_text.lower() in item.content.lower() else 0.4
            
            if similarity >= query.min_similarity:
                results.append(item)
                
        return results

    def get_all(self) -> List[MemoryItem]:
        return list(self._db.values())
