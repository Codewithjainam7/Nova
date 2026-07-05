import time
import asyncio
from backend.island.schema import IslandEvent, IslandSession, IslandConfiguration, IslandMetrics, IslandStateType, IslandNotification, IslandNotificationType
from backend.island.presentation import IslandRenderer, IslandAnimator, IslandNotificationManager, IslandInteractionManager
from backend.core.logger import app_logger

class IslandLogger:
    @staticmethod
    def log_event(event: IslandEvent):
        app_logger.info(f"[ISLAND EVENT] {event.source} -> {event.state.name}")

class IslandStateManager:
    """Maintains the unified ViewModel state of the Island."""
    def __init__(self):
        self.state = IslandStateType.IDLE
        self.active_widgets = []

    def update(self, new_state: IslandStateType):
        self.state = new_state

class IslandEventSubscriber:
    """Listens to Kernel events and routes them to the Island."""
    def __init__(self, manager: 'IslandManager'):
        self.manager = manager
        
    async def handle_event(self, event: IslandEvent):
        IslandLogger.log_event(event)
        await self.manager.process_event(event)

class IslandManager:
    def __init__(self, config: IslandConfiguration):
        self.config = config
        self.state_manager = IslandStateManager()
        self.animator = IslandAnimator()
        self.notifications = IslandNotificationManager()
        self.renderer = IslandRenderer(self.animator, self.notifications)
        self.interaction = IslandInteractionManager()

    async def process_event(self, event: IslandEvent):
        # Update logical state
        self.state_manager.update(event.state)
        
        # Trigger UI Render
        await self.renderer.render_state(event.state, event.payload)
        
        # Check for error notifications
        if event.state == IslandStateType.ERROR:
            msg = event.payload.get("error_msg", "An unknown error occurred.")
            notif = IslandNotification(type=IslandNotificationType.ERROR, message=msg)
            await self.notifications.show(notif)

class DynamicIsland:
    """Central entrypoint for the Dynamic Island presentation subsystem."""
    def __init__(self):
        self.config = IslandConfiguration()
        self.metrics = IslandMetrics()
        self.session = IslandSession()
        self.manager = IslandManager(self.config)
        self.subscriber = IslandEventSubscriber(self.manager)

    async def dispatch_kernel_event(self, event: IslandEvent):
        """Called by the Event Bus to push state to the UI."""
        start = time.time()
        
        await self.subscriber.handle_event(event)
        
        self.metrics.total_events_processed += 1
        elapsed = (time.time() - start) * 1000
        self._update_metric("avg_render_latency_ms", elapsed)
        
    async def dispatch_user_interaction(self, action: str, payload: dict):
        """Called when User clicks/drags the Island."""
        await self.manager.interaction.handle_interaction(action, payload)

    def _update_metric(self, attr: str, elapsed: float):
        n = self.metrics.total_events_processed
        if n > 0:
            current = getattr(self.metrics, attr)
            new_val = ((current * (n - 1)) + elapsed) / n
            setattr(self.metrics, attr, new_val)
