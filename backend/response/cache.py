from typing import Dict, Optional
from backend.response.schema import ResponseOutput

class ResponseCache:
    """Basic cache for response generation to avoid reprocessing."""
    def __init__(self):
        self._cache: Dict[str, ResponseOutput] = {}

    def get(self, checksum: str) -> Optional[ResponseOutput]:
        return self._cache.get(checksum)

    def set(self, checksum: str, output: ResponseOutput):
        self._cache[checksum] = output
