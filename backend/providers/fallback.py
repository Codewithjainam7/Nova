from typing import List, Optional
from backend.providers.schema import ProviderType
from backend.providers.registry import ProviderRegistry
from backend.providers.interface import ProviderInterface

class FallbackManager:
    def __init__(self, registry: ProviderRegistry):
        self.registry = registry

    def get_fallback(self, failed_provider: ProviderType) -> Optional[ProviderInterface]:
        """Get the next best provider when one fails."""
        priority = [ProviderType.GEMINI, ProviderType.OPENROUTER, ProviderType.OLLAMA, ProviderType.MOCK]
        
        try:
            current_index = priority.index(failed_provider)
        except ValueError:
            current_index = -1
            
        for p in priority[current_index + 1:]:
            provider = self.registry.get_provider(p)
            if provider:
                return provider
                
        return None
