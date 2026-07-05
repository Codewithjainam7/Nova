from typing import List
import asyncio

class AudioBuffer:
    """Manages raw audio chunks for processing."""
    def __init__(self, max_size: int = 1024 * 1024): # 1MB limit by default
        self.buffer = bytearray()
        self.max_size = max_size
        self._lock = asyncio.Lock()

    async def write(self, data: bytes):
        async with self._lock:
            if len(self.buffer) + len(data) > self.max_size:
                # Naive ring buffer approach - drop oldest
                excess = (len(self.buffer) + len(data)) - self.max_size
                self.buffer = self.buffer[excess:]
            self.buffer.extend(data)

    async def read_all(self) -> bytes:
        async with self._lock:
            data = bytes(self.buffer)
            self.buffer.clear()
            return data

    async def clear(self):
        async with self._lock:
            self.buffer.clear()
