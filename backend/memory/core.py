import time
from typing import List, Optional
from backend.memory.schema import MemoryItem, MemoryQuery, MemoryMetrics, MemoryPolicy
from backend.memory.store import MemoryStore, MemoryCache
from backend.memory.embedder import MemoryEmbedder
from backend.memory.ranker import MemoryRanker
from backend.memory.retriever import MemoryRetriever
from backend.memory.consolidator import MemoryConsolidator, MemorySummarizer
from backend.memory.cleaner import MemoryCleaner
from backend.core.logger import app_logger

class MemoryLogger:
    @staticmethod
    def log_operation(op: str, memory_id: str, mem_type: str):
        app_logger.info(f"[MEMORY {op}] ID: {memory_id}, Type: {mem_type}")

class MemoryManager:
    """Internal orchestration of memory operations."""
    def __init__(self, store: MemoryStore, cache: MemoryCache, embedder: MemoryEmbedder):
        self.store = store
        self.cache = cache
        self.embedder = embedder
        
    async def store_memory(self, item: MemoryItem):
        # Generate embedding
        item.embedding = await self.embedder.embed(item.content)
        
        # Save to DB and Cache
        await self.store.add(item)
        self.cache.set(item)
        MemoryLogger.log_operation("STORED", item.memory_id, item.memory_type.name)

    async def get_memory(self, memory_id: str) -> Optional[MemoryItem]:
        cached = self.cache.get(memory_id)
        if cached:
            return cached
            
        item = await self.store.get(memory_id)
        if item:
            self.cache.set(item)
            MemoryLogger.log_operation("RETRIEVED", item.memory_id, item.memory_type.name)
        return item

    async def update_memory(self, item: MemoryItem):
        # Optional: Re-embed if content changed
        await self.store.update(item)
        self.cache.set(item)
        MemoryLogger.log_operation("UPDATED", item.memory_id, item.memory_type.name)

    async def delete_memory(self, memory_id: str):
        await self.store.delete(memory_id)
        self.cache.delete(memory_id)
        MemoryLogger.log_operation("DELETED", memory_id, "UNKNOWN")

class MemoryEngine:
    """Central entrypoint for all memory interactions."""
    def __init__(self):
        self.policy = MemoryPolicy()
        self.metrics = MemoryMetrics()
        
        self.store = MemoryStore()
        self.cache = MemoryCache()
        self.embedder = MemoryEmbedder()
        self.ranker = MemoryRanker()
        
        self.manager = MemoryManager(self.store, self.cache, self.embedder)
        self.retriever = MemoryRetriever(self.store, self.cache, self.embedder, self.ranker)
        
        self.summarizer = MemorySummarizer()
        self.consolidator = MemoryConsolidator(self.store, self.summarizer)
        self.cleaner = MemoryCleaner(self.store, self.cache, self.policy)

    async def add(self, item: MemoryItem):
        await self.manager.store_memory(item)
        self.metrics.total_memories += 1

    async def get(self, memory_id: str) -> Optional[MemoryItem]:
        return await self.manager.get_memory(memory_id)

    async def update(self, item: MemoryItem):
        await self.manager.update_memory(item)

    async def forget(self, memory_id: str):
        await self.manager.delete_memory(memory_id)
        self.metrics.total_memories -= 1

    async def search(self, query: MemoryQuery) -> List[MemoryItem]:
        start = time.time()
        try:
            results = await self.retriever.retrieve(query)
            self.metrics.total_retrievals += 1
            return results
        finally:
            elapsed = (time.time() - start) * 1000
            n = self.metrics.total_retrievals
            if n > 0:
                self.metrics.avg_retrieval_ms = ((self.metrics.avg_retrieval_ms * (n - 1)) + elapsed) / n

    async def run_maintenance(self):
        """Called periodically to consolidate and clean memory."""
        await self.consolidator.consolidate()
        await self.cleaner.clean()
