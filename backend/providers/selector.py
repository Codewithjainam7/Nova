from typing import List, Optional
from backend.providers.schema import ProviderType, CognitiveDomain
from backend.providers.registry import ProviderRegistry
from backend.providers.interface import ProviderInterface

class ProviderSelector:
    """Selects best provider based on cognitive domain, configuration, or priority."""
    def __init__(self, registry: ProviderRegistry):
        self.registry = registry

    def select(self, force_provider: Optional[ProviderType] = None, domain: Optional[CognitiveDomain] = None) -> ProviderInterface:
        if force_provider:
            provider = self.registry.get_provider(force_provider)
            if provider:
                return provider

        # Domain-specialized priority hierarchy
        if domain == CognitiveDomain.REFLEX:
            priority = [ProviderType.GROQ, ProviderType.OPENROUTER, ProviderType.GEMINI]
        elif domain == CognitiveDomain.SOCIAL_SYNTHESIS:
            priority = [ProviderType.GROQ, ProviderType.GEMINI, ProviderType.OPENROUTER]
        elif domain == CognitiveDomain.DEEP_PLANNING:
            priority = [ProviderType.GROQ, ProviderType.OPENROUTER, ProviderType.GEMINI]
        elif domain == CognitiveDomain.VISION:
            priority = [ProviderType.OPENROUTER, ProviderType.GEMINI]
        else:
            # Default: Groq for speed if available, then OpenRouter, then Gemini
            priority = [ProviderType.GROQ, ProviderType.OPENROUTER, ProviderType.GEMINI, ProviderType.OLLAMA, ProviderType.MOCK]

        for p in priority:
            provider = self.registry.get_provider(p)
            if provider:
                return provider
                
        raise RuntimeError("No AI providers available in registry")
