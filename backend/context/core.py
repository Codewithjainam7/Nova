import asyncio
from backend.context.schema import ContextPackage
from backend.context.collector import ContextCollector, ContextProvider
from backend.context.pipeline import ContextPipeline
from backend.core.logger import app_logger

class ContextMetrics:
    def __init__(self):
        self.total_packages_built = 0
        self.avg_tokens = 0.0

class ContextEngine:
    """
    Central orchestration for Context building.
    Collects, ranks, filters, compresses, and assembles context before sending to AI Provider.
    """
    def __init__(self, max_tokens: int = 4000):
        self.collector = ContextCollector()
        self.pipeline = ContextPipeline(collector=self.collector, max_tokens=max_tokens)
        self.metrics = ContextMetrics()

    def register_provider(self, provider: ContextProvider):
        """Allows system to register new context sources (e.g. Memory, Browser, OS)."""
        self.collector.register_provider(provider)

    async def get_context(self) -> ContextPackage:
        """Runs the pipeline and returns the final Context Package."""
        try:
            package = await self.pipeline.build_context()
            
            # Update metrics
            self.metrics.total_packages_built += 1
            n = self.metrics.total_packages_built
            self.metrics.avg_tokens = ((self.metrics.avg_tokens * (n - 1)) + package.total_estimated_tokens) / n
            
            app_logger.debug(f"Built context package {package.context_id}.")
            return package
        except Exception as e:
            app_logger.error(f"Failed to build context: {str(e)}")
            # Return empty safe context instead of crashing
            return ContextPackage()
