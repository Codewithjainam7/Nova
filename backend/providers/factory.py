from backend.providers.schema import ProviderType
from backend.providers.interface import ProviderInterface
from backend.providers.adapters.gemini import GeminiProvider
from backend.providers.adapters.groq import GroqProvider

class ProviderFactory:
    @staticmethod
    def create(p_type: ProviderType) -> ProviderInterface:
        if p_type == ProviderType.GEMINI:
            return GeminiProvider()
        elif p_type == ProviderType.GROQ:
            return GroqProvider()
        raise ValueError(f"Unknown ProviderType: {p_type}")
