import asyncio
from typing import List
from backend.core.logger import app_logger

# Import lazily or globally based on preference. 
# SentenceTransformer takes a bit to load, so doing it at the module level caches it.
try:
    import os
    os.environ["HF_HUB_OFFLINE"] = "1"
    from sentence_transformers import SentenceTransformer
    # We use all-MiniLM-L6-v2 as requested for fast, local embeddings
    _model = SentenceTransformer('all-MiniLM-L6-v2', local_files_only=True)
except ImportError:
    _model = None
    app_logger.warning("sentence-transformers not installed. Embedder will fail.")

class MemoryEmbedder:
    """Handles embedding generation using sentence-transformers."""
    
    def __init__(self):
        if _model is None:
            raise RuntimeError("sentence-transformers is not available.")
            
    async def embed(self, text: str) -> List[float]:
        app_logger.debug(f"Generating embeddings for: {text[:20]}...")
        # SentenceTransformer.encode is synchronous and can be CPU bound.
        # Run it in a thread pool so we don't block the asyncio event loop.
        loop = asyncio.get_event_loop()
        embedding = await loop.run_in_executor(None, _model.encode, text)
        # Convert numpy array to list of floats
        return embedding.tolist()
