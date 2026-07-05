from typing import Dict, Any
from backend.prompt.schema import PromptTemplate, PromptRequest
from backend.core.logger import app_logger

class PromptPolicy:
    """Defines limits and rules for prompts."""
    max_tokens: int = 120000 # Configurable limit

class PromptValidator:
    def __init__(self, policy: PromptPolicy):
        self.policy = policy

    def validate_variables(self, template: PromptTemplate, variables: Dict[str, Any]) -> bool:
        missing = [v for v in template.required_variables if v not in variables]
        if missing:
            app_logger.error(f"Missing required variables for prompt template {template.name}: {missing}")
            return False
        return True

    def validate_rendered(self, rendered_content: str) -> bool:
        # Dummy token validation
        estimated_tokens = len(rendered_content) // 4
        if estimated_tokens > self.policy.max_tokens:
            app_logger.error(f"Rendered prompt exceeds max tokens ({estimated_tokens} > {self.policy.max_tokens})")
            return False
        return True
