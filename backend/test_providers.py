import asyncio
import pytest
import os
from backend.core.environment import load_environment
load_environment()

from backend.providers.schema import ProviderType, GenerationRequest, Message, Role
from backend.providers.core import AIProviderManager
from backend.providers.factory import ProviderFactory

def setup_manager():
    manager = AIProviderManager()
    manager.registry.register_provider(ProviderFactory.create(ProviderType.GEMINI))
    manager.registry.register_provider(ProviderFactory.create(ProviderType.GROQ))
    # Configure fallback Gemini -> Groq for tests
    manager.fallback_manager.register_fallback(ProviderType.GEMINI, ProviderType.GROQ)
    return manager

@pytest.mark.asyncio
async def test_provider_registration():
    manager = setup_manager()
    assert len(manager.registry.list_providers()) == 2
    assert manager.registry.get_provider(ProviderType.GEMINI) is not None
    assert manager.registry.get_provider(ProviderType.GROQ) is not None

@pytest.mark.asyncio
async def test_generation_success():
    manager = setup_manager()
    request = GenerationRequest(
        messages=[Message(role=Role.USER, content="Hello, respond with exactly 'Hello'")],
        provider_type=ProviderType.GEMINI,
        temperature=0.0,
        model=""
    )
    
    response = await manager.generate(request)
    assert response.content is not None
    assert response.provider_used == ProviderType.GEMINI
    assert manager.metrics.token_tracker.usage_by_provider[ProviderType.GEMINI].total_tokens > 0

@pytest.mark.asyncio
async def test_streaming_success():
    manager = setup_manager()
    request = GenerationRequest(
        messages=[Message(role=Role.USER, content="Hello, count from 1 to 3.")],
        provider_type=ProviderType.GEMINI,
        stream=True,
        temperature=0.0,
        model=""
    )
    
    tokens = []
    async for chunk in manager.generate_stream(request):
        tokens.append(chunk.token)
        
    assert len("".join(tokens)) > 0

@pytest.mark.asyncio
async def test_provider_fallback():
    manager = setup_manager()
    
    # Break Gemini intentionally by raising an Exception in generate
    gemini_provider = manager.registry.get_provider(ProviderType.GEMINI)
    async def fake_generate(*args, **kwargs):
        raise Exception("Intentional Gemini Failure")
    gemini_provider.generate = fake_generate
    
    request = GenerationRequest(
        messages=[Message(role=Role.USER, content="Hello, respond with exactly 'Fallback'")],
        provider_type=ProviderType.GEMINI,
        retry_count=0,
        model=""
    )
    
    response = await manager.generate(request)
    assert response.content is not None
    assert response.provider_used == ProviderType.GROQ
    assert manager.metrics.fallbacks_triggered == 1

if __name__ == "__main__":
    asyncio.run(test_provider_registration())
    asyncio.run(test_generation_success())
    asyncio.run(test_streaming_success())
    asyncio.run(test_provider_fallback())
    print("ALL AI PROVIDER TESTS PASSED")
