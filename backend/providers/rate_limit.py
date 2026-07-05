import asyncio
from backend.providers.schema import ProviderType
from backend.core.logger import app_logger

class RateLimitManager:
    """Mock rate limiter. Real one would track RPM/TPM per provider."""
    async def wait_if_needed(self, provider: ProviderType):
        # Simulated wait for rate limit
        await asyncio.sleep(0.01)
