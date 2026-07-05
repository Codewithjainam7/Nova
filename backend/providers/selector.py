from typing import List
from backend.providers.schema import ProviderType
from backend.providers.registry import ProviderRegistry
from backend.providers.interface import ProviderInterface

class ProviderSelector:
    """Selects best provider based on configuration or priority."""
    def __init__(self, registry: ProviderRegistry):
        self.registry = registry

    def select(self, force_provider: ProviderType = None) -> ProviderInterface:
        if force_provider:
            provider = self.registry.get_provider(force_provider)
            if provider:
                return provider
                
        # Default priority fallback logic for selection
        priority = [ProviderType.GEMINI, ProviderType.OPENROUTER, ProviderType.OLLAMA, ProviderType.MOCK]
        for p in priority:
            provider = self.registry.get_provider(p)
            if provider:
                return provider
                
        raise RuntimeError("No AI providers available in registry")
