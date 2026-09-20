import time
import hashlib
from typing import Dict
from backend.prompt.schema import PromptRequest, PromptOutput, PromptMetrics
from backend.prompt.template import PromptTemplateRegistry, PromptTemplateLoader, PromptVersionManager
from backend.prompt.resolver import PromptVariableResolver
from backend.prompt.builder import PromptBuilder, PromptAssembler
from backend.prompt.optimizer import PromptOptimizer, PromptCompressor
from backend.prompt.validator import PromptValidator, PromptPolicy
from backend.prompt.cache import PromptCache
from backend.core.logger import app_logger

class PromptAuditLogger:
    @staticmethod
    def log_generation(output: PromptOutput):
        app_logger.debug(f"[PROMPT GENERATED] Type: {output.prompt_type}")

class PromptManager:
    """Core class handling prompt execution pipeline."""
    def __init__(self, registry: PromptTemplateRegistry):
        self.registry = registry
        self.resolver = PromptVariableResolver()
        self.compressor = PromptCompressor()
        self.optimizer = PromptOptimizer(self.compressor)
        self.assembler = PromptAssembler()
        self.builder = PromptBuilder(self.resolver, self.optimizer, self.assembler)
        self.policy = PromptPolicy()
        self.validator = PromptValidator(self.policy)
        self.cache = PromptCache()

    def _generate_checksum(self, template_id: str, variables: Dict) -> str:
        # A deterministic way to check if we've rendered exactly this before
        raw = f"{template_id}-" + "-".join(f"{k}:{v}" for k, v in sorted(variables.items()))
        return hashlib.sha256(raw.encode()).hexdigest()

    async def generate(self, request: PromptRequest) -> PromptOutput:
        template = self.registry.get_template(request.prompt_type)
        if not template:
            raise ValueError(f"No template registered for {request.prompt_type}")

        variables = self.resolver.resolve(request)
        
        if not self.validator.validate_variables(template, variables):
            raise ValueError("Failed variable validation")

        # Cache check
        req_hash = self._generate_checksum(template.template_id, variables)
        cached = self.cache.get(req_hash)
        if cached:
            return cached

        rendered = self.builder.render(template, variables)
        optimized = self.optimizer.optimize(rendered, request.provider_target)
        
        if not self.validator.validate_rendered(optimized):
            raise ValueError("Failed post-render validation")

        estimated_tokens = len(optimized) // 4
        
        output = self.assembler.assemble(template, optimized, request, estimated_tokens)
        self.cache.set(req_hash, output)
        
        PromptAuditLogger.log_generation(output)
        return output

class PromptEngine:
    """Central entrypoint for prompting."""
    def __init__(self):
        self.version_manager = PromptVersionManager()
        self.registry = PromptTemplateRegistry(self.version_manager)
        self.loader = PromptTemplateLoader(self.registry)
        self.manager = PromptManager(self.registry)
        self.metrics = PromptMetrics()

        self.loader.load_defaults()

    async def build_prompt(self, request: PromptRequest) -> PromptOutput:
        start = time.time()
        try:
            output = await self.manager.generate(request)
            
            # Update metrics
            self.metrics.total_prompts_generated += 1
            self.metrics.total_tokens_estimated += output.estimated_tokens
            # simplistic cache miss tracking (real cache tracking is deeper)
            self.metrics.cache_misses += 1 
            
            return output
        except Exception as e:
            app_logger.error(f"Prompt generation failed: {str(e)}")
            raise
        finally:
            elapsed = (time.time() - start) * 1000
            n = self.metrics.total_prompts_generated
            if n > 0:
                self.metrics.avg_generation_time_ms = ((self.metrics.avg_generation_time_ms * (n - 1)) + elapsed) / n
