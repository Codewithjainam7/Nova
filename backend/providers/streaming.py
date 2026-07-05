import asyncio
from typing import AsyncGenerator
from backend.providers.schema import StreamingToken
from backend.core.logger import app_logger

class StreamingManager:
    """Manages stream timeouts and cancellation."""
    @staticmethod
    async def process_stream(stream: AsyncGenerator[StreamingToken, None], timeout: float) -> AsyncGenerator[StreamingToken, None]:
        try:
            async for chunk in stream:
                # In a real implementation we would enforce chunk timeouts here
                yield chunk
        except asyncio.TimeoutError:
            app_logger.error(f"Stream timed out after {timeout} seconds")
            raise
        except Exception as e:
            app_logger.error(f"Stream error: {str(e)}")
            raise
