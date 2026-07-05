import asyncio
from typing import Callable, Dict, List, Any
from dataclasses import dataclass
from datetime import datetime
from backend.core.logger import app_logger

@dataclass
class Event:
    topic: str
    payload: Any
    priority: int = 1
    timestamp: datetime = None

    def __post_init__(self):
        if self.timestamp is None:
            self.timestamp = datetime.utcnow()

class EventBus:
    """
    Async Event Bus for pub/sub architecture.
    Supports priorities and maintains event history.
    """
    def __init__(self):
        self._subscribers: Dict[str, List[Callable]] = {}
        self._history: List[Event] = []

    def subscribe(self, topic: str, callback: Callable):
        if topic not in self._subscribers:
            self._subscribers[topic] = []
        self._subscribers[topic].append(callback)
        app_logger.debug(f"Subscribed to topic: {topic}")

    async def publish(self, topic: str, payload: Any = None, priority: int = 1):
        event = Event(topic=topic, payload=payload, priority=priority)
        self._history.append(event)
        
        # Limit history size
        if len(self._history) > 1000:
            self._history.pop(0)

        subscribers = self._subscribers.get(topic, [])
        if not subscribers:
            app_logger.debug(f"No subscribers for event: {topic}")
            return

        app_logger.debug(f"Publishing event {topic} to {len(subscribers)} subscribers")
        
        # Execute callbacks asynchronously
        tasks = []
        for callback in subscribers:
            if asyncio.iscoroutinefunction(callback):
                tasks.append(asyncio.create_task(callback(event)))
            else:
                try:
                    callback(event)
                except Exception as e:
                    app_logger.error(f"Error in synchronous event handler for {topic}: {e}")

        if tasks:
            await asyncio.gather(*tasks, return_exceptions=True)

    def get_history(self) -> List[Event]:
        return self._history

event_bus = EventBus()
