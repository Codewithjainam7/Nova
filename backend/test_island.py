import asyncio
import pytest
from backend.island.schema import IslandEvent, IslandStateType
from backend.island.core import DynamicIsland

@pytest.mark.asyncio
async def test_island_event_processing():
    island = DynamicIsland()
    
    event = IslandEvent(
        source="ExecutionEngine",
        state=IslandStateType.EXECUTING,
        payload={"task": "Navigating Browser"}
    )
    
    await island.dispatch_kernel_event(event)
    
    assert island.metrics.total_events_processed == 1
    assert island.manager.state_manager.state == IslandStateType.EXECUTING

@pytest.mark.asyncio
async def test_island_error_notification():
    island = DynamicIsland()
    
    event = IslandEvent(
        source="VoiceEngine",
        state=IslandStateType.ERROR,
        payload={"error_msg": "Microphone disconnected"}
    )
    
    await island.dispatch_kernel_event(event)
    
    assert len(island.manager.notifications.active_notifications) == 1
    assert island.manager.notifications.active_notifications[0].message == "Microphone disconnected"

@pytest.mark.asyncio
async def test_island_user_interaction():
    island = DynamicIsland()
    
    # Simulate user clicking a quick action
    await island.dispatch_user_interaction("CLICK", {"widget": "CancelAction"})
    
    # Interaction shouldn't increment kernel events
    assert island.metrics.total_events_processed == 0

if __name__ == "__main__":
    asyncio.run(test_island_event_processing())
    asyncio.run(test_island_error_notification())
    asyncio.run(test_island_user_interaction())
    print("ALL ISLAND TESTS PASSED")
