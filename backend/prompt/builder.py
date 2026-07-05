from typing import Dict, Any
import hashlib
from backend.prompt.schema import PromptTemplate, PromptOutput, PromptRequest
from backend.prompt.resolver import PromptVariableResolver
from backend.prompt.optimizer import PromptOptimizer
from backend.core.logger import app_logger

class PromptAssembler:
    """Actually constructs the output object."""
    def assemble(self, template: PromptTemplate, rendered: str, request: PromptRequest, estimated_tokens: int) -> PromptOutput:
        checksum = hashlib.sha256(rendered.encode()).hexdigest()
        
        return PromptOutput(
            prompt_version=template.version,
            prompt_type=request.prompt_type,
            rendered_prompt=rendered,
            estimated_tokens=estimated_tokens,
            provider_target=request.provider_target,
            template_used=template.name,
            checksum=checksum
        )

class PromptBuilder:
    """Builds the string from the template and variables."""
    def __init__(self, resolver: PromptVariableResolver, optimizer: PromptOptimizer, assembler: PromptAssembler):
        self.resolver = resolver
        self.optimizer = optimizer
        self.assembler = assembler

    def render(self, template: PromptTemplate, variables: Dict[str, Any]) -> str:
        try:
            return template.content.format(**variables)
        except KeyError as e:
            app_logger.error(f"Failed to render prompt: Missing variable in format - {str(e)}")
            raise
