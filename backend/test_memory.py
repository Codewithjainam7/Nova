import asyncio
import pytest
from datetime import datetime, timedelta
from backend.memory.schema import MemoryItem, MemoryType, MemoryQuery
from backend.memory.core import MemoryEngine

@pytest.mark.asyncio
async def test_memory_store_and_retrieve():
    engine = MemoryEngine()
    
    item = MemoryItem(
        memory_type=MemoryType.WORKING_MEMORY,
        content="The user's favorite color is blue."
    )
    
    # Store
    await engine.add(item)
    
    # Retrieve directly
    retrieved = await engine.get(item.memory_id)
    assert retrieved is not None
    assert retrieved.content == "The user's favorite color is blue."
    assert retrieved.embedding is not None  # Automatically generated

@pytest.mark.asyncio
async def test_memory_search():
    engine = MemoryEngine()
    
    await engine.add(MemoryItem(memory_type=MemoryType.WORKING_MEMORY, content="Alpha context data."))
    await engine.add(MemoryItem(memory_type=MemoryType.LONG_TERM_MEMORY, content="Beta context data."))
    
    query = MemoryQuery(query_text="Alpha", min_similarity=0.1)
    results = await engine.search(query)
    
    assert len(results) > 0
    # Search simulated: "Alpha" matches "Alpha context data." exactly in naive mock
    assert "Alpha" in results[0].content

@pytest.mark.asyncio
async def test_memory_cleanup():
    engine = MemoryEngine()
    
    # Create an expired item
    item = MemoryItem(
        memory_type=MemoryType.WORKING_MEMORY,
        content="Old temporary thought",
        expires_at=datetime.now() - timedelta(hours=1)
    )
    await engine.add(item)
    
    # Run cleanup
    await engine.run_maintenance()
    
    # Should be deleted
    retrieved = await engine.get(item.memory_id)
    assert retrieved is None

if __name__ == "__main__":
    asyncio.run(test_memory_store_and_retrieve())
    asyncio.run(test_memory_search())
    asyncio.run(test_memory_cleanup())
    print("ALL MEMORY TESTS PASSED")
