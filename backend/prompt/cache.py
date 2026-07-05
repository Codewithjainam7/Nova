from typing import Dict, Optional
from backend.prompt.schema import PromptOutput

class PromptCache:
    """Basic cache for prompt generation."""
    def __init__(self):
        self._cache: Dict[str, PromptOutput] = {}

    def get(self, checksum: str) -> Optional[PromptOutput]:
        return self._cache.get(checksum)

    def set(self, checksum: str, output: PromptOutput):
        self._cache[checksum] = output
