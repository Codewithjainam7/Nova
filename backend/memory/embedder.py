import asyncio
import hashlib
from typing import List
from backend.core.logger import app_logger

# Import lazily or globally based on preference. 
# SentenceTransformer takes a bit to load, so doing it at the module level caches it.
_model = None
try:
    import os
    os.environ["HF_HUB_OFFLINE"] = "1"
    from sentence_transformers import SentenceTransformer
    # We use all-MiniLM-L6-v2 as requested for fast, local embeddings
    _model = SentenceTransformer('all-MiniLM-L6-v2', local_files_only=True)
except Exception as exc:
    _model = None
    app_logger.warning(f"SentenceTransformer not available or model not cached: {exc}. Using deterministic fallback embedder.")

class MemoryEmbedder:
    """Handles embedding generation using sentence-transformers or deterministic fallback."""
    
    def __init__(self):
        pass
            
    async def embed(self, text: str) -> List[float]:
        app_logger.debug(f"Generating embeddings for: {text[:20]}...")
        if _model is not None:
            try:
                loop = asyncio.get_event_loop()
                embedding = await loop.run_in_executor(None, _model.encode, text)
                return embedding.tolist()
            except Exception as e:
                app_logger.warning(f"Model encode failed ({e}), falling back to deterministic vector.")

        # Deterministic 384-dimensional fallback vector based on sha256
        h = hashlib.sha256(text.encode('utf-8')).digest()
        vec = [round(((h[i % len(h)] + (i * 13) % 256) / 255.0) * 2.0 - 1.0, 6) for i in range(384)]
        return vec
