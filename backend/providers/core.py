import asyncio
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

    def bootstrap(self):
        """Register default/configured providers."""
        gemini_provider = ProviderFactory.create(ProviderType.GEMINI)
        groq_provider = ProviderFactory.create(ProviderType.GROQ)
        
        self.registry.register_provider(gemini_provider)
        self.registry.register_provider(groq_provider)
        
        # Configure fallback Gemini -> Groq
        self.fallback_manager.register_fallback(ProviderType.GEMINI, ProviderType.GROQ)

    async def generate(self, request: GenerationRequest) -> GenerationResponse:
        """Standard unary generation with fallback."""
        provider = self.selector.select(request.provider_type)
        retries_left = request.retry_count
        
        while retries_left >= 0:
            try:
                self.metrics.requests_made += 1
                await self.rate_limiter.wait_if_needed(provider.provider_type)
                
                app_logger.debug(f"Calling provider {provider.provider_type.value}")
                
                response = await asyncio.wait_for(provider.generate(request), timeout=request.timeout)
                
                # Record metrics
                self.metrics.token_tracker.record_usage(provider.provider_type, response.usage)
                return response
                
            except asyncio.TimeoutError:
                app_logger.error(f"Provider {provider.provider_type.value} timed out")
                retries_left -= 1
            except Exception as e:
                app_logger.error(f"Provider {provider.provider_type.value} failed: {str(e)}")
                retries_left -= 1
                
            if retries_left < 0:
                # Trigger Fallback
                self.metrics.fallbacks_triggered += 1
                fallback_provider = self.fallback_manager.get_fallback(provider.provider_type)
                if fallback_provider:
                    app_logger.warning(f"Failing over to {fallback_provider.provider_type.value}")
                    provider = fallback_provider
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
