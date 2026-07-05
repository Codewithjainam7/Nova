from typing import Callable, Dict, List, Any
from enum import Enum
import asyncio

class KernelEventType(str, Enum):
    KERNEL_STARTED = "KERNEL_STARTED"
    REQUEST_RECEIVED = "REQUEST_RECEIVED"
    PLANNING_STARTED = "PLANNING_STARTED"
    EXECUTION_STARTED = "EXECUTION_STARTED"
    VERIFICATION_STARTED = "VERIFICATION_STARTED"
    CONTEXT_BUILT = "CONTEXT_BUILT"
    PROVIDER_INVOKED = "PROVIDER_INVOKED"
    STREAMING_STARTED = "STREAMING_STARTED"
    RESPONSE_COMPLETED = "RESPONSE_COMPLETED"
    SESSION_CLOSED = "SESSION_CLOSED"
    ERROR = "ERROR"

class KernelEventBus:
    """Simple pub/sub event bus for the Kernel."""
    def __init__(self):
        self._subscribers: Dict[KernelEventType, List[Callable]] = {
            event_type: [] for event_type in KernelEventType
        }

    def subscribe(self, event_type: KernelEventType, callback: Callable):
        self._subscribers[event_type].append(callback)

    async def publish(self, event_type: KernelEventType, payload: Any = None):
        callbacks = self._subscribers.get(event_type, [])
        for cb in callbacks:
            if asyncio.iscoroutinefunction(cb):
                await cb(payload)
            else:
                cb(payload)
