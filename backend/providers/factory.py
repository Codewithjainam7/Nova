from backend.providers.schema import ProviderType
from backend.providers.interface import ProviderInterface
from backend.providers.adapters.mock import MockProvider
from backend.providers.adapters.gemini import GeminiProvider
from backend.providers.adapters.openrouter import OpenRouterProvider
from backend.providers.adapters.ollama import OllamaProvider

class ProviderFactory:
    @staticmethod
    def create(p_type: ProviderType) -> ProviderInterface:
        if p_type == ProviderType.MOCK:
            return MockProvider()
        elif p_type == ProviderType.GEMINI:
            return GeminiProvider()
        elif p_type == ProviderType.OPENROUTER:
            return OpenRouterProvider()
        elif p_type == ProviderType.OLLAMA:
            return OllamaProvider()
        raise ValueError(f"Unknown ProviderType: {p_type}")
