from typing import List
from backend.context.schema import ContextItem
from backend.core.logger import app_logger

class ContextCompressor:
    def __init__(self, max_tokens: int = 4000):
        self.max_tokens = max_tokens

    def compress(self, items: List[ContextItem]) -> List[ContextItem]:
        """
        Greedy compression: keep adding items from top to bottom (assuming pre-ranked)
        until max_tokens limit is reached.
        """
        compressed = []
        current_tokens = 0
        
        for item in items:
            # Fake token estimation for now. A real system uses tiktoken or similar.
            estimated = len(str(item.content)) // 4
            item.estimated_tokens = estimated
            
            if current_tokens + estimated <= self.max_tokens:
                compressed.append(item)
                current_tokens += estimated
            else:
                # We reached limit, skip the rest
                app_logger.debug(f"Context compression dropped remaining items to stay under limit.")
                break
                
        return compressed
