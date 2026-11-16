import asyncio
import time
from typing import AsyncGenerator
from backend.providers.schema import GenerationRequest, GenerationResponse, StreamingToken, ProviderType
from backend.providers.registry import ProviderRegistry
from backend.providers.factory import ProviderFactory
from backend.providers.metrics import ProviderMetrics
from backend.providers.rate_limit import RateLimitManager
from backend.providers.fallback import FallbackManager
from backend.providers.selector import ProviderSelector
from backend.providers.streaming import StreamingManager
from backend.providers.health import ProviderHealthMonitor
from backend.core.logger import app_logger

class AIProviderManager:
    """
    Central orchestration for all AI / LLM Provider communications.
    No other subsystem calls LLMs directly.
    """
    def __init__(self):
        self.registry = ProviderRegistry()
        self.metrics = ProviderMetrics()
        self.rate_limiter = RateLimitManager()
        self.fallback_manager = FallbackManager(self.registry)
        self.selector = ProviderSelector(self.registry)
        self.streaming_manager = StreamingManager()
        self.health_monitor = ProviderHealthMonitor(self.registry)
        self._cooldowns = {}

    def bootstrap(self):
        """Register default/configured providers."""
        try:
            openrouter_provider = ProviderFactory.create(ProviderType.OPENROUTER)
            self.registry.register_provider(openrouter_provider)
        except Exception as e:
            app_logger.warning(f"Failed to bootstrap OpenRouter: {e}")

        try:
            groq_provider = ProviderFactory.create(ProviderType.GROQ)
            self.registry.register_provider(groq_provider)
        except Exception as e:
            app_logger.warning(f"Failed to bootstrap Groq: {e}")

        try:
            gemini_provider = ProviderFactory.create(ProviderType.GEMINI)
            self.registry.register_provider(gemini_provider)
        except Exception as e:
            app_logger.warning(f"Failed to bootstrap Gemini: {e}")
        
        # Configure multi-model fallback cascade: OpenRouter <-> Groq <-> Gemini
        self.fallback_manager.register_fallback(ProviderType.OPENROUTER, ProviderType.GROQ)
        self.fallback_manager.register_fallback(ProviderType.GROQ, ProviderType.GEMINI)
        self.fallback_manager.register_fallback(ProviderType.GEMINI, ProviderType.OPENROUTER)

    def _default_model_for_provider(self, provider_type: ProviderType) -> str:
        import os
        if provider_type == ProviderType.GROQ:
            return os.getenv("GROQ_DEFAULT_MODEL", "openai/gpt-oss-120b")
        elif provider_type == ProviderType.GEMINI:
            return os.getenv("GEMINI_DEFAULT_MODEL", "gemini-3.5-flash")
        elif provider_type == ProviderType.OPENROUTER:
            return os.getenv("OPENROUTER_DEFAULT_MODEL", "nvidia/nemotron-3.5-super-vl:free")
        return "default"

    async def generate(self, request: GenerationRequest) -> GenerationResponse:
        """Standard unary generation with fallback and cognitive domain selection."""
        target_type = request.provider_type
        domain = getattr(request, "cognitive_domain", None)

        # If requested provider is on cooldown, select fallback directly
        if target_type and time.time() < self._cooldowns.get(target_type, 0):
            fallback_p = self.fallback_manager.get_fallback(target_type)
            if fallback_p:
                app_logger.info(f"Provider {target_type.value} is on rate-limit cooldown. Using {fallback_p.provider_type.value}")
                provider = fallback_p
            else:
                provider = self.selector.select(force_provider=target_type, domain=domain)
        else:
            provider = self.selector.select(force_provider=target_type, domain=domain)

        # Ensure model is valid for the chosen provider
        if not request.model or (target_type and provider.provider_type != target_type):
            request.model = self._default_model_for_provider(provider.provider_type)

        retries_left = request.retry_count
        
        while retries_left >= 0:
            try:
                self.metrics.requests_made += 1
                await self.rate_limiter.wait_if_needed(provider.provider_type)
                
                app_logger.debug(f"Calling provider {provider.provider_type.value} (model: {request.model})")
                
                response = await asyncio.wait_for(provider.generate(request), timeout=request.timeout)
                
                # Record metrics
                self.metrics.token_tracker.record_usage(provider.provider_type, response.usage)
                return response
                
            except asyncio.TimeoutError:
                app_logger.error(f"Provider {provider.provider_type.value} timed out. Triggering immediate failover.")
                retries_left = -1
            except Exception as e:
                err_msg = str(e)
                app_logger.error(f"Provider {provider.provider_type.value} failed: {err_msg}")
                # Immediate failover on rate limits / quota exhaustion
                if "429" in err_msg or "RESOURCE_EXHAUSTED" in err_msg or "quota" in err_msg.lower():
                    app_logger.warning(f"Rate limit exceeded for {provider.provider_type.value}. Applying 10m cooldown.")
                    self._cooldowns[provider.provider_type] = time.time() + 600
                    retries_left = -1
                else:
                    retries_left -= 1
                
            if retries_left < 0:
                # Trigger Fallback
                self.metrics.fallbacks_triggered += 1
                fallback_provider = self.fallback_manager.get_fallback(provider.provider_type)
                if fallback_provider and fallback_provider != provider:
                    app_logger.warning(f"Failing over from {provider.provider_type.value} to {fallback_provider.provider_type.value}")
                    provider = fallback_provider
                    request.model = self._default_model_for_provider(provider.provider_type)
                    retries_left = request.retry_count # Reset retries for new provider
                else:
                    app_logger.critical("All providers exhausted.")
                    raise RuntimeError("All AI providers failed.")
                    
    async def generate_stream(self, request: GenerationRequest) -> AsyncGenerator[StreamingToken, None]:
        """Streaming generation with failover."""
        provider = self.selector.select(request.provider_type)
        
        try:
            self.metrics.requests_made += 1
            await self.rate_limiter.wait_if_needed(provider.provider_type)
            app_logger.debug(f"Streaming from provider {provider.provider_type.value}")
            
            raw_stream = provider.generate_stream(request)
            
            async for chunk in self.streaming_manager.process_stream(raw_stream, request.timeout):
                if chunk.is_final and chunk.usage:
                    self.metrics.token_tracker.record_usage(provider.provider_type, chunk.usage)
                yield chunk
                
        except Exception as e:
            app_logger.error(f"Streaming failed on {provider.provider_type.value}: {str(e)}")
            # Fallback logic for streaming is complex (we can't just restart if partial data sent)
            # For simplicity, raise the error.
            raise
