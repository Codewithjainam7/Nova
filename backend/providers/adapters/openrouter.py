from typing import AsyncGenerator
from backend.providers.interface import ProviderInterface
from backend.providers.schema import GenerationRequest, GenerationResponse, StreamingToken, ProviderType

class OpenRouterProvider(ProviderInterface):
    @property
    def provider_type(self) -> ProviderType:
        return ProviderType.OPENROUTER
        
    async def check_health(self) -> bool:
        # Stub
        return False

    async def generate(self, request: GenerationRequest) -> GenerationResponse:
        raise NotImplementedError("OpenRouter provider not fully implemented")

    async def generate_stream(self, request: GenerationRequest) -> AsyncGenerator[StreamingToken, None]:
        raise NotImplementedError("OpenRouter provider not fully implemented")
        yield
