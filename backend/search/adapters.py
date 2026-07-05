import asyncio
from typing import List
from backend.search.schema import SearchQuery, SearchResult, SearchProviderType
from backend.core.logger import app_logger

class WebSearchAdapter:
    async def search(self, query: SearchQuery) -> List[SearchResult]:
        app_logger.debug(f"[WEB] Searching for: {query.text}")
        await asyncio.sleep(0.5)
        return [
            SearchResult(
                title=f"Web Result for {query.text}",
                url="https://example.com/web",
                snippet="Mock web result snippet.",
                provider=SearchProviderType.WEB,
                relevance_score=0.8,
                authority_score=0.9,
                freshness_score=0.5
            )
        ]

class NewsAdapter:
    async def search(self, query: SearchQuery) -> List[SearchResult]:
        app_logger.debug(f"[NEWS] Searching for: {query.text}")
        await asyncio.sleep(0.4)
        return [
            SearchResult(
                title=f"News Result for {query.text}",
                url="https://example.com/news",
                snippet="Mock news result snippet.",
                provider=SearchProviderType.NEWS,
                relevance_score=0.7,
                authority_score=0.8,
                freshness_score=0.95
            )
        ]

class DocumentationSearchAdapter:
    async def search(self, query: SearchQuery) -> List[SearchResult]:
        app_logger.debug(f"[DOCS] Searching for: {query.text}")
        await asyncio.sleep(0.3)
        return []

class AcademicSearchAdapter:
    async def search(self, query: SearchQuery) -> List[SearchResult]:
        app_logger.debug(f"[ACADEMIC] Searching for: {query.text}")
        await asyncio.sleep(0.6)
        return []

class LocalSearchAdapter:
    async def search(self, query: SearchQuery) -> List[SearchResult]:
        app_logger.debug(f"[LOCAL] Searching for: {query.text}")
        await asyncio.sleep(0.1)
        return []

class SearchProviderRegistry:
    def __init__(self):
        self._providers = {}
        
    def register(self, provider_type: SearchProviderType, adapter):
        self._providers[provider_type] = adapter
        
    def get(self, provider_type: SearchProviderType):
        return self._providers.get(provider_type)

class SearchProviderFactory:
    @staticmethod
    def create_registry() -> SearchProviderRegistry:
        registry = SearchProviderRegistry()
        registry.register(SearchProviderType.WEB, WebSearchAdapter())
        registry.register(SearchProviderType.NEWS, NewsAdapter())
        registry.register(SearchProviderType.DOCUMENTATION, DocumentationSearchAdapter())
        registry.register(SearchProviderType.ACADEMIC, AcademicSearchAdapter())
        registry.register(SearchProviderType.LOCAL, LocalSearchAdapter())
        return registry
