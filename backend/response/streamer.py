from typing import AsyncGenerator
from backend.core.logger import app_logger

class ResponseStreamer:
    """Handles async chunk merging from the provider streaming."""
    def __init__(self):
        pass

    async def aggregate(self, stream: AsyncGenerator[str, None]) -> str:
        """Consumes a stream of string chunks and returns the fully aggregated string."""
        aggregated = []
        try:
            async for chunk in stream:
                if chunk:
                    aggregated.append(chunk)
        except Exception as e:
            app_logger.error(f"Error during stream aggregation: {str(e)}")
            raise
            
        return "".join(aggregated)
