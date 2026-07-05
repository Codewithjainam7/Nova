from typing import Dict, Type
from backend.verification.strategies import VerificationStrategy

class VerificationRegistry:
    def __init__(self):
        self._strategies: Dict[str, VerificationStrategy] = {}

    def register_strategy(self, strategy: VerificationStrategy):
        self._strategies[strategy.strategy_name] = strategy

    def get_strategy(self, name: str) -> VerificationStrategy:
        return self._strategies.get(name)

    def list_strategies(self) -> list[VerificationStrategy]:
        return list(self._strategies.values())
