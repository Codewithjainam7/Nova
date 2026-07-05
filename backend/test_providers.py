import asyncio
import pytest
from backend.providers.schema import ProviderType, GenerationRequest, Message, Role
from backend.providers.core import AIProviderManager
from backend.providers.factory import ProviderFactory

def setup_manager():
    manager = AIProviderManager()
    manager.registry.register_provider(ProviderFactory.create(ProviderType.GEMINI))
    manager.registry.register_provider(ProviderFactory.create(ProviderType.MOCK))
    return manager

@pytest.mark.asyncio
async def test_provider_registration():
    manager = setup_manager()
    assert len(manager.registry.list_providers()) == 2
    assert manager.registry.get_provider(ProviderType.MOCK) is not None

@pytest.mark.asyncio
async def test_generation_success():
    manager = setup_manager()
    request = GenerationRequest(
        messages=[Message(role=Role.USER, content="Hello")],
        model="mock-model",
        provider_type=ProviderType.MOCK
    )
    
    response = await manager.generate(request)
    assert response.content == "This is a mocked response."
    assert response.provider_used == ProviderType.MOCK
    assert manager.metrics.token_tracker.usage_by_provider[ProviderType.MOCK].total_tokens == 15

@pytest.mark.asyncio
async def test_streaming_success():
    manager = setup_manager()
    request = GenerationRequest(
        messages=[Message(role=Role.USER, content="Stream me")],
        model="mock-model",
        provider_type=ProviderType.MOCK,
        stream=True
    )
    
    tokens = []
    async for chunk in manager.generate_stream(request):
        tokens.append(chunk.token)
        
    assert "".join(tokens) == "This is a mocked streaming response."
    assert manager.metrics.token_tracker.usage_by_provider[ProviderType.MOCK].total_tokens >= 15

@pytest.mark.asyncio
async def test_provider_fallback():
    manager = setup_manager()
    # Gemini throws NotImplementedError in our stub, so calling it should fail
    # and it should fallback to MOCK
    request = GenerationRequest(
        messages=[Message(role=Role.USER, content="Fallback")],
        model="gemini-model",
        provider_type=ProviderType.GEMINI,
        retry_count=0
    )
    
    response = await manager.generate(request)
    # The manager caught the failure, fell back to MOCK, and MOCK succeeded.
    assert response.content == "This is a mocked response."
    assert response.provider_used == ProviderType.MOCK
    assert manager.metrics.fallbacks_triggered == 1

if __name__ == "__main__":
    asyncio.run(test_provider_registration())
    asyncio.run(test_generation_success())
    asyncio.run(test_streaming_success())
    asyncio.run(test_provider_fallback())
    print("ALL AI PROVIDER TESTS PASSED")
