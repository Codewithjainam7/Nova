from typing import AsyncGenerator
from backend.providers.interface import ProviderInterface
from backend.providers.schema import GenerationRequest, GenerationResponse, StreamingToken, ProviderType

class GeminiProvider(ProviderInterface):
    @property
    def provider_type(self) -> ProviderType:
        return ProviderType.GEMINI
        
    async def check_health(self) -> bool:
        # Stub
        return False

    async def generate(self, request: GenerationRequest) -> GenerationResponse:
        raise NotImplementedError("Gemini provider not fully implemented")

    async def generate_stream(self, request: GenerationRequest) -> AsyncGenerator[StreamingToken, None]:
        raise NotImplementedError("Gemini provider not fully implemented")
        yield # Make it a generator
