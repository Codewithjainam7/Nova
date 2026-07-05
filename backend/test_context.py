import asyncio
import pytest
from typing import List
from backend.context.schema import ContextItem, ContextType
from backend.context.collector import ContextProvider
from backend.context.core import ContextEngine

class MockSystemProvider(ContextProvider):
    async def collect(self) -> List[ContextItem]:
        return [
            ContextItem(type=ContextType.SYSTEM, content="Time: 12:00", relevance_score=1.0, importance=1.0),
            ContextItem(type=ContextType.SYSTEM, content="Pref: Dark Mode", relevance_score=0.5, importance=0.8)
        ]

class MockMemoryProvider(ContextProvider):
    async def collect(self) -> List[ContextItem]:
        return [
            ContextItem(type=ContextType.LONG_TERM_MEMORY, content="User likes Rust", relevance_score=0.9),
            # Duplicate item to test deduplication
            ContextItem(type=ContextType.LONG_TERM_MEMORY, content="User likes Rust", relevance_score=0.9),
            # Low relevance item to test filtering
            ContextItem(type=ContextType.LONG_TERM_MEMORY, content="User ate apple", relevance_score=0.1)
        ]

@pytest.mark.asyncio
async def test_context_pipeline():
    engine = ContextEngine(max_tokens=100) # Small limit
    engine.register_provider(MockSystemProvider())
    engine.register_provider(MockMemoryProvider())

    package = await engine.get_context()
    
    # Verify assembly
    assert len(package.preference_context) == 2
    
    # Deduplication and Filtering (0.1 should be filtered out, duplicate should be removed)
    assert len(package.memory_context) == 1
    assert package.memory_context[0].content == "User likes Rust"
    
    # Token estimation (our dummy logic is len // 4)
    assert package.total_estimated_tokens > 0
    assert package.total_estimated_tokens <= 100

@pytest.mark.asyncio
async def test_context_compression():
    engine = ContextEngine(max_tokens=4) # Extremely tight limit
    engine.register_provider(MockSystemProvider())
    
    # Expected logic: "Time: 12:00" length 11 -> 2 tokens. "Pref: Dark Mode" length 15 -> 3 tokens.
    # Total = 5 tokens. Max is 4. One should be dropped.
    package = await engine.get_context()
    
    assert len(package.preference_context) == 1
    assert package.preference_context[0].content == "Time: 12:00" # Should be ranked higher (1.0 vs 0.5 rel)
    
if __name__ == "__main__":
    asyncio.run(test_context_pipeline())
    asyncio.run(test_context_compression())
    print("ALL CONTEXT TESTS PASSED")
