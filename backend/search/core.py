import time
import asyncio
from typing import List, Optional
from datetime import datetime, timedelta
from backend.search.schema import SearchQuery, SearchResult, SearchSession, SearchMetrics, SearchConfiguration
from backend.search.adapters import SearchProviderFactory
from backend.search.processing import SearchRanker, SearchVerifier
from backend.core.logger import app_logger

class SearchLogger:
    @staticmethod
    def log_query(query: SearchQuery, status: str):
        app_logger.info(f"[SEARCH - {status}] Query: {query.text}")

class SearchCache:
    def __init__(self, ttl_seconds: int):
        self.ttl = ttl_seconds
        self._cache = {}
        
    def get(self, query_text: str) -> Optional[List[SearchResult]]:
        entry = self._cache.get(query_text)
        if entry:
            timestamp, results = entry
            if (datetime.now() - timestamp).total_seconds() < self.ttl:
                return results
            else:
                del self._cache[query_text]
        return None
        
    def set(self, query_text: str, results: List[SearchResult]):
        self._cache[query_text] = (datetime.now(), results)

class SearchQueryBuilder:
    @staticmethod
    def build(text: str) -> SearchQuery:
        # Complex query expansion logic could go here
        return SearchQuery(text=text)

class SearchPipeline:
    def __init__(self, registry, ranker, verifier):
        self.registry = registry
        self.ranker = ranker
        self.verifier = verifier

    async def run(self, query: SearchQuery) -> List[SearchResult]:
        all_results = []
        
        # Parallel execution of all requested providers
        tasks = []
        for provider_type in query.providers:
            adapter = self.registry.get(provider_type)
            if adapter:
                tasks.append(adapter.search(query))
                
        if tasks:
            results_sets = await asyncio.gather(*tasks, return_exceptions=True)
            for res_set in results_sets:
                if isinstance(res_set, list):
                    all_results.extend(res_set)
                else:
                    app_logger.error(f"Provider failed: {str(res_set)}")
                    
        # Rank
        ranked = await self.ranker.rank(all_results)
        
        # Verify top results
        top_k = ranked[:query.max_results]
        verified = await self.verifier.verify(top_k)
        
        return verified

class SearchManager:
    def __init__(self, config: SearchConfiguration):
        self.config = config
        self.registry = SearchProviderFactory.create_registry()
        self.ranker = SearchRanker(config)
        self.verifier = SearchVerifier()
        self.cache = SearchCache(config.cache_ttl_seconds)
        self.pipeline = SearchPipeline(self.registry, self.ranker, self.verifier)

class SearchExecutor:
    def __init__(self, manager: SearchManager, metrics: SearchMetrics, session: SearchSession):
        self.manager = manager
        self.metrics = metrics
        self.session = session

    async def execute(self, query: SearchQuery) -> List[SearchResult]:
        start = time.time()
        SearchLogger.log_query(query, "START")
        
        try:
            # Check Cache
            if self.manager.config.enable_caching:
                cached = self.manager.cache.get(query.text)
                if cached:
                    self.metrics.cache_hits += 1
                    SearchLogger.log_query(query, "CACHE HIT")
                    return cached
            
            # Run Pipeline
            results = await self.manager.pipeline.run(query)
            
            # Save to Cache
            if self.manager.config.enable_caching:
                self.manager.cache.set(query.text, results)
                
            # History
            self.session.history.append(query)
            
            SearchLogger.log_query(query, "SUCCESS")
            self.metrics.total_queries += 1
            
            elapsed = (time.time() - start) * 1000
            self._update_metric("avg_search_latency_ms", elapsed)
            
            return results
            
        except Exception as e:
            SearchLogger.log_query(query, f"FAILED: {str(e)}")
            self.metrics.failed_queries += 1
            raise

    def _update_metric(self, attr: str, elapsed: float):
        n = self.metrics.total_queries
        if n > 0:
            current = getattr(self.metrics, attr)
            new_val = ((current * (n - 1)) + elapsed) / n
            setattr(self.metrics, attr, new_val)

class SearchEngine:
    """Central entrypoint for Search capabilities."""
    def __init__(self):
        self.config = SearchConfiguration()
        self.metrics = SearchMetrics()
        self.session = SearchSession()
        self.manager = SearchManager(self.config)
        self.executor = SearchExecutor(self.manager, self.metrics, self.session)

    async def search(self, query_text: str, providers: List[str] = None) -> List[SearchResult]:
        """Main search API."""
        query = SearchQueryBuilder.build(query_text)
        if providers:
            # Simple mapping, in a real scenario we'd map string to enum properly
            from backend.search.schema import SearchProviderType
            mapped = []
            for p in providers:
                try:
                    mapped.append(SearchProviderType[p])
                except KeyError:
                    pass
            query.providers = mapped
            
        return await self.executor.execute(query)
