from typing import List
from backend.context.schema import ContextItem
from backend.core.logger import app_logger

class ContextFilter:
    """Filters out context items based on thresholds or duplication."""
    def __init__(self, relevance_threshold: float = 0.3):
        self.relevance_threshold = relevance_threshold

    def deduplicate(self, items: List[ContextItem]) -> List[ContextItem]:
        seen = set()
        unique = []
        for item in items:
            # We hash the content if possible to detect exact duplicates
            try:
                content_hash = hash(str(item.content))
                if content_hash not in seen:
                    seen.add(content_hash)
                    unique.append(item)
            except Exception:
                unique.append(item) # fallback, just append
        return unique

    def filter_by_threshold(self, items: List[ContextItem]) -> List[ContextItem]:
        filtered = [item for item in items if item.relevance_score >= self.relevance_threshold]
        if len(items) != len(filtered):
            app_logger.debug(f"Filtered out {len(items) - len(filtered)} context items.")
        return filtered
