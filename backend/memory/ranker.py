from typing import List
from backend.memory.schema import MemoryItem
from datetime import datetime

class MemoryRanker:
    """Ranks memories based on hybrid scoring (similarity, recency, importance)."""
    
    def rank(self, items: List[MemoryItem], base_similarities: List[float]) -> List[MemoryItem]:
        ranked = []
        now = datetime.now()
        
        for idx, item in enumerate(items):
            sim = base_similarities[idx] if idx < len(base_similarities) else 0.5
            
            # Recency factor: newer is better (naive implementation)
            age_seconds = (now - item.last_accessed_at).total_seconds()
            recency_score = max(0.0, 1.0 - (age_seconds / 86400)) # Decays over a day
            
            # Hybrid Score formula
            final_score = (sim * 0.5) + (recency_score * 0.3) + (item.importance * 0.2)
            
            ranked.append((final_score, item))
            
        ranked.sort(key=lambda x: x[0], reverse=True)
        return [r[1] for r in ranked]
