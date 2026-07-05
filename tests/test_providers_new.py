import asyncio
import sys

from backend.core.environment import load_environment
load_environment()

from backend.providers.schema import ProviderType, GenerationRequest, Message, Role
from backend.providers.core import AIProviderManager

async def test_providers():
    print("=== Task 5: Provider Verification ===")
    provider_manager = AIProviderManager()
    provider_manager.bootstrap()
    
    registry = provider_manager.registry
    providers = getattr(registry, '_providers', {})
    has_providers = len(providers) > 0
    print(f"Registry not empty: {has_providers}")
    gemini_registered = ProviderType.GEMINI in providers
    print(f"Gemini registered: {gemini_registered}")
    groq_registered = ProviderType.GROQ in providers
    print(f"Groq registered: {groq_registered}")
    print()
    
    print("=== Task 6: Real API Verification ===")
    req = GenerationRequest(
        messages=[Message(role=Role.USER, content="Hello NOVA")],
        model="",
        stream=True
    )
    
    # In AIProviderManager, if provider_type is None, it defaults to active_provider (Gemini usually)
    req.provider_type = ProviderType.GEMINI
    
    try:
        print("Testing Gemini Streaming...")
        gen = provider_manager.generate_stream(req)
        
        chunk_count = 0
        final_usage = None
        async for token in gen:
            print(token.token, end="", flush=True)
            chunk_count += 1
            if token.usage:
                final_usage = token.usage
                
        print(f"\n\nGemini [PASS]")
        print(f"Streaming token count: {chunk_count}")
        print(f"Usage metrics: {final_usage}")
        
    except Exception as e:
        print(f"\nGemini FAILED: {e}")
        print("Automatically verifying fallback to Groq...")
        
    print("Testing Groq Streaming...")
    req.provider_type = ProviderType.GROQ
    try:
        gen = provider_manager.generate_stream(req)
        
        chunk_count = 0
        final_usage = None
        async for token in gen:
            print(token.token, end="", flush=True)
            chunk_count += 1
            if token.usage:
                final_usage = token.usage
                
        print(f"\n\nGroq [PASS]")
        print(f"Streaming token count: {chunk_count}")
        print(f"Usage metrics: {final_usage}")
    except Exception as fallback_e:
        print(f"\nGroq FAILED: {fallback_e}")

if __name__ == "__main__":
    asyncio.run(test_providers())
