from abc import ABC, abstractmethod
from typing import AsyncGenerator
from backend.providers.schema import GenerationRequest, GenerationResponse, StreamingToken, ProviderType

class ProviderInterface(ABC):
    @property
    @abstractmethod
    def provider_type(self) -> ProviderType:
        pass

    @abstractmethod
    async def check_health(self) -> bool:
        pass

    @abstractmethod
    async def generate(self, request: GenerationRequest) -> GenerationResponse:
        pass

    @abstractmethod
    async def generate_stream(self, request: GenerationRequest) -> AsyncGenerator[StreamingToken, None]:
        pass
