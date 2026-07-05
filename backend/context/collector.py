from typing import List, Any
from abc import ABC, abstractmethod
from backend.context.schema import ContextItem

class ContextProvider(ABC):
    @abstractmethod
    async def collect(self) -> List[ContextItem]:
        pass

class ContextCollector:
    def __init__(self):
        self._providers: List[ContextProvider] = []

    def register_provider(self, provider: ContextProvider):
        self._providers.append(provider)

    async def collect_all(self) -> List[ContextItem]:
        all_items = []
        for provider in self._providers:
            try:
                items = await provider.collect()
                all_items.extend(items)
            except Exception:
                # We log this in a real system. Silent fail to not block context.
                pass
        return all_items
