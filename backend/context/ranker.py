from typing import List
from backend.context.schema import ContextItem

class ContextRanker:
    """Ranks context based on relevance, recency, and importance."""
    @staticmethod
    def rank(items: List[ContextItem]) -> List[ContextItem]:
        # Weighted score: 50% relevance, 30% recency, 20% importance
        def get_score(item: ContextItem) -> float:
            return (item.relevance_score * 0.5) + (item.recency_score * 0.3) + (item.importance * 0.2)

        return sorted(items, key=get_score, reverse=True)
