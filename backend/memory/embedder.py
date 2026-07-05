from typing import List
from backend.core.logger import app_logger

class MemoryEmbedder:
    """Handles embedding generation (e.g. ONNX, SentenceTransformers)."""
    async def embed(self, text: str) -> List[float]:
        # Dummy embedding for prototype
        app_logger.debug(f"Generating embeddings for: {text[:20]}...")
        return [0.1, 0.2, 0.3, 0.4]
