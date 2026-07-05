from typing import List, Dict, Optional
from backend.memory.schema import MemoryItem, MemoryQuery, MemoryType
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

from backend.memory.sqlite_store import SQLiteStore
from backend.memory.chroma_store import ChromaVectorStore

class MemoryStore:
    """Facade for the Hybrid Database (SQLite + ChromaDB)."""
    def __init__(self):
        self.sqlite = SQLiteStore()
        self.chroma = ChromaVectorStore()

    def _is_vector_memory(self, item_type: MemoryType) -> bool:
        """Determines if a memory type should be indexed in ChromaDB."""
        # Typically long-term, semantic, preference, etc.
        # Conversations and raw Working Memory might skip vectorization depending on policy.
        # We index everything with an embedding for robustness.
        return True

    async def add(self, item: MemoryItem):
        # 1. Save metadata to SQLite
        self.sqlite.save_memory_metadata(item)
        # 2. Save vector to Chroma if applicable
        if item.embedding and self._is_vector_memory(item.memory_type):
            await self.chroma.add(item)
        
    async def get(self, memory_id: str) -> Optional[MemoryItem]:
        # SQLite is the source of truth for the full reconstructed item
        return self.sqlite.get_memory_metadata(memory_id)

    async def update(self, item: MemoryItem):
        self.sqlite.save_memory_metadata(item)
        if item.embedding and self._is_vector_memory(item.memory_type):
            await self.chroma.update(item)

    async def delete(self, memory_id: str):
        self.sqlite.delete_memory_metadata(memory_id)
        # We can fire and forget delete to chroma, it won't crash if id doesn't exist
        try:
            await self.chroma.delete(memory_id)
        except Exception:
            pass

    async def search(self, query: MemoryQuery, query_embedding: List[float]) -> List[MemoryItem]:
        """Hybrid Search: Vector search -> Hydrate from SQLite."""
        matched_ids = await self.chroma.search(query, query_embedding)
        
        results = []
        for mem_id in matched_ids:
            item = self.sqlite.get_memory_metadata(mem_id)
            if item:
                results.append(item)
                
        return results

    def get_all(self) -> List[MemoryItem]:
        return self.sqlite.get_all_memory_metadata()
