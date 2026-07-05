import asyncio
import pytest
from backend.search.schema import SearchProviderType
from backend.search.core import SearchEngine

@pytest.mark.asyncio
async def test_search_pipeline():
    engine = SearchEngine()
    
    # Simple web search
    results = await engine.search("What is the capital of France?", providers=["WEB", "NEWS"])
    
    assert len(results) > 0
    assert engine.metrics.total_queries == 1
    assert results[0].verified == True

@pytest.mark.asyncio
async def test_search_cache():
    engine = SearchEngine()
    
    # First search (miss)
    await engine.search("Test query")
    assert engine.metrics.total_queries == 1
    assert engine.metrics.cache_hits == 0
    
    # Second search (hit)
    await engine.search("Test query")
    assert engine.metrics.cache_hits == 1

@pytest.mark.asyncio
async def test_search_history():
    engine = SearchEngine()
    
    await engine.search("History test")
    assert len(engine.session.history) == 1
    assert engine.session.history[0].text == "History test"

if __name__ == "__main__":
    asyncio.run(test_search_pipeline())
    asyncio.run(test_search_cache())
    asyncio.run(test_search_history())
    print("ALL SEARCH TESTS PASSED")
