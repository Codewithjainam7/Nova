from backend.memory.schema import MemoryPolicy
from backend.memory.store import MemoryStore, MemoryCache
from backend.core.logger import app_logger
from datetime import datetime

class MemoryCleaner:
    """Handles expiration, compression, and deletion based on policy."""
    def __init__(self, store: MemoryStore, cache: MemoryCache, policy: MemoryPolicy):
        self.store = store
        self.cache = cache
        self.policy = policy

    async def clean(self):
        app_logger.info("Running memory cleanup routine.")
        all_items = self.store.get_all()
        now = datetime.now()
        
        for item in all_items:
            # Check expiration
            if item.expires_at and now > item.expires_at:
                await self.store.delete(item.memory_id)
                self.cache.delete(item.memory_id)
                app_logger.debug(f"Deleted expired memory: {item.memory_id}")
            
            # Check importance retention
            elif item.importance < self.policy.importance_threshold:
                # E.g. we might delete it if it's very old and unimportant
                pass
