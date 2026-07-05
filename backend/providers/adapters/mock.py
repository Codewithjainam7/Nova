import asyncio
from typing import AsyncGenerator
from backend.providers.interface import ProviderInterface
from backend.providers.schema import GenerationRequest, GenerationResponse, StreamingToken, ProviderType, UsageMetrics

class MockProvider(ProviderInterface):
    @property
    def provider_type(self) -> ProviderType:
        return ProviderType.MOCK
        
    async def check_health(self) -> bool:
        return True

    async def generate(self, request: GenerationRequest) -> GenerationResponse:
        await asyncio.sleep(0.1) # Simulate network
        
        return GenerationResponse(
            content="This is a mocked response.",
            provider_used=self.provider_type,
            model_used=request.model,
            usage=UsageMetrics(prompt_tokens=10, completion_tokens=5, total_tokens=15, estimated_cost=0.0001)
        )

    async def generate_stream(self, request: GenerationRequest) -> AsyncGenerator[StreamingToken, None]:
        words = ["This ", "is ", "a ", "mocked ", "streaming ", "response."]
        for i, word in enumerate(words):
            await asyncio.sleep(0.05)
            is_final = (i == len(words) - 1)
            yield StreamingToken(
                token=word,
                is_final=is_final,
                provider_used=self.provider_type if is_final else None,
                model_used=request.model if is_final else None,
                usage=UsageMetrics(prompt_tokens=10, completion_tokens=len(words), total_tokens=10+len(words), estimated_cost=0.0001) if is_final else None
            )
