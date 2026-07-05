import asyncio
from typing import List
from backend.search.schema import SearchResult, SearchConfiguration
from backend.core.logger import app_logger

class SearchRanker:
    def __init__(self, config: SearchConfiguration):
        self.config = config

    async def rank(self, results: List[SearchResult]) -> List[SearchResult]:
        app_logger.debug(f"Ranking {len(results)} search results.")
        await asyncio.sleep(0.05) # Simulated ranking latency
        
        for res in results:
            # Hybrid score calculation
            res.final_score = (
                (res.relevance_score * self.config.semantic_ranking_weight) +
                (res.freshness_score * self.config.freshness_ranking_weight) +
                (res.authority_score * self.config.authority_ranking_weight)
            )
            
        # Sort descending by final score
        ranked_results = sorted(results, key=lambda x: x.final_score, reverse=True)
        
        # Simple deduplication by URL
        seen = set()
        deduped = []
        for r in ranked_results:
            if r.url not in seen:
                seen.add(r.url)
                deduped.append(r)
                
        return deduped

class SearchVerifier:
    async def verify(self, results: List[SearchResult]) -> List[SearchResult]:
        app_logger.debug(f"Verifying {len(results)} search results.")
        await asyncio.sleep(0.1) # Simulated verification latency
        
        verified_results = []
        for res in results:
            # Simulate a verification check (e.g., checking if link is not 404)
            res.verified = True
            verified_results.append(res)
            
        return verified_results
