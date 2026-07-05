from typing import Dict, List, Optional
from backend.providers.interface import ProviderInterface
from backend.providers.schema import ProviderType
from backend.core.logger import app_logger

class ProviderRegistry:
    def __init__(self):
        self._providers: Dict[ProviderType, ProviderInterface] = {}

    def register_provider(self, provider: ProviderInterface):
        self._providers[provider.provider_type] = provider
        app_logger.info(f"Registered AI Provider: {provider.provider_type.value}")

    def remove_provider(self, p_type: ProviderType):
        if p_type in self._providers:
            del self._providers[p_type]
            app_logger.info(f"Removed AI Provider: {p_type.value}")

    def get_provider(self, p_type: ProviderType) -> Optional[ProviderInterface]:
        return self._providers.get(p_type)

    def list_providers(self) -> List[ProviderInterface]:
        return list(self._providers.values())
