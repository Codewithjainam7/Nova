from typing import Dict
from backend.providers.schema import ProviderType, UsageMetrics

class CostTracker:
    def __init__(self):
        self.total_cost: float = 0.0
        
    def add_cost(self, cost: float):
        self.total_cost += cost

class TokenUsageTracker:
    def __init__(self):
        self.usage_by_provider: Dict[ProviderType, UsageMetrics] = {}
        
    def record_usage(self, provider: ProviderType, usage: UsageMetrics):
        if provider not in self.usage_by_provider:
            self.usage_by_provider[provider] = UsageMetrics()
            
        current = self.usage_by_provider[provider]
        current.prompt_tokens += usage.prompt_tokens
        current.completion_tokens += usage.completion_tokens
        current.total_tokens += usage.total_tokens
        current.estimated_cost += usage.estimated_cost

class ProviderMetrics:
    def __init__(self):
        self.token_tracker = TokenUsageTracker()
        self.cost_tracker = CostTracker()
        self.requests_made = 0
        self.fallbacks_triggered = 0
