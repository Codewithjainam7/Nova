from typing import List, Optional
from backend.providers.schema import ProviderType
from backend.providers.registry import ProviderRegistry
from backend.providers.interface import ProviderInterface

class FallbackManager:
    def __init__(self, registry: ProviderRegistry):
        self.registry = registry
        self.fallback_map = {}

    def register_fallback(self, primary: ProviderType, fallback: ProviderType):
        self.fallback_map[primary] = fallback

    def get_fallback(self, failed_provider: ProviderType) -> Optional[ProviderInterface]:
        """Get the next best provider when one fails."""
        fallback_type = self.fallback_map.get(failed_provider)
        if fallback_type:
            return self.registry.get_provider(fallback_type)
            
        priority = [ProviderType.GEMINI, ProviderType.GROQ]
        
        try:
            current_index = priority.index(failed_provider)
        except ValueError:
            current_index = -1
            
        for p in priority[current_index + 1:]:
            provider = self.registry.get_provider(p)
            if provider:
                return provider
                
        return None
