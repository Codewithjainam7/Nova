import asyncio
from typing import List
from backend.island.schema import IslandEvent, IslandAnimationType, IslandNotification, IslandNotificationType, IslandStateType
from backend.core.logger import app_logger

class IslandAnimator:
    """Manages logical animation states to send to the frontend."""
    async def animate(self, animation: IslandAnimationType, duration_ms: int):
        app_logger.debug(f"[ISLAND] Triggering animation: {animation.name} for {duration_ms}ms")
        await asyncio.sleep(0.01) # Non-blocking

class IslandNotificationManager:
    def __init__(self):
        self.active_notifications: List[IslandNotification] = []

    async def show(self, notification: IslandNotification):
        app_logger.info(f"[ISLAND NOTIFICATION] {notification.type.name}: {notification.message}")
        self.active_notifications.append(notification)
        await asyncio.sleep(0.01)
        
    def clear(self, notification_id: str):
        self.active_notifications = [n for n in self.active_notifications if n.notification_id != notification_id]

class IslandInteractionManager:
    """Handles inputs from the frontend Island UI (Clicks, Drags)."""
    async def handle_interaction(self, action: str, payload: dict):
        app_logger.debug(f"[ISLAND INTERACTION] {action} -> {payload}")
        await asyncio.sleep(0.01)

class IslandRenderer:
    """Translates backend events into frontend ViewModel updates."""
    def __init__(self, animator: IslandAnimator, notifications: IslandNotificationManager):
        self.animator = animator
        self.notifications = notifications
        self.current_state = IslandStateType.IDLE

    async def render_state(self, state: IslandStateType, payload: dict):
        if self.current_state != state:
            self.current_state = state
            app_logger.debug(f"[ISLAND RENDER] Transitioning to {state.name}")
            
            # Map state to animation
            if state == IslandStateType.LISTENING:
                await self.animator.animate(IslandAnimationType.GLOW, 500)
            elif state == IslandStateType.PROCESSING:
                await self.animator.animate(IslandAnimationType.PULSE, 1000)
            elif state == IslandStateType.EXECUTING:
                await self.animator.animate(IslandAnimationType.PROGRESS, 1000)
            elif state == IslandStateType.ERROR:
                await self.animator.animate(IslandAnimationType.FADE, 300)
            else:
                await self.animator.animate(IslandAnimationType.COLLAPSE, 300)
