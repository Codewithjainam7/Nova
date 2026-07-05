from backend.providers.registry import ProviderRegistry
from backend.providers.schema import ProviderType
from backend.core.logger import app_logger

class ProviderHealthMonitor:
    def __init__(self, registry: ProviderRegistry):
        self.registry = registry

    async def check_all(self):
        for provider in self.registry.list_providers():
            try:
                is_healthy = await provider.check_health()
                app_logger.debug(f"Provider {provider.provider_type.value} health: {is_healthy}")
            except Exception as e:
                app_logger.error(f"Provider {provider.provider_type.value} health check failed: {str(e)}")
