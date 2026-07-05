import asyncio
import pytest
from backend.desktop.schema import DesktopAction, DesktopActionType, DesktopPermissionLevel
from backend.desktop.core import DesktopEngine

@pytest.mark.asyncio
async def test_desktop_action_execution():
    engine = DesktopEngine()
    
    action = DesktopAction(
        action_type=DesktopActionType.MOUSE_MOVE,
        payload={"x": 100, "y": 200}
    )
    
    await engine.perform_action(action)
    assert engine.metrics.total_actions == 1
    assert engine.metrics.avg_mouse_latency_ms > 0

@pytest.mark.asyncio
async def test_desktop_permissions():
    # Set to READ_ONLY
    engine = DesktopEngine(permission_level=DesktopPermissionLevel.READ_ONLY)
    
    action = DesktopAction(
        action_type=DesktopActionType.FS_WRITE,
        payload={"path": "C:/test.txt"}
    )
    
    with pytest.raises(PermissionError):
        await engine.perform_action(action)
        
    assert engine.metrics.failed_actions == 1

@pytest.mark.asyncio
async def test_desktop_recovery_on_failure():
    engine = DesktopEngine()
    
    # We will simulate a failure in the dispatcher
    async def failing_dispatch(action):
        raise RuntimeError("Simulated OS API failure")
        
    engine.manager.dispatcher.dispatch = failing_dispatch
    
    action = DesktopAction(
        action_type=DesktopActionType.APP_LAUNCH,
        payload={"path": "notepad.exe"}
    )
    
    with pytest.raises(RuntimeError):
        await engine.perform_action(action)
        
    # The recovery manager would have caught it and logged it before re-raising
    assert engine.metrics.failed_actions == 1

if __name__ == "__main__":
    asyncio.run(test_desktop_action_execution())
    asyncio.run(test_desktop_permissions())
    asyncio.run(test_desktop_recovery_on_failure())
    print("ALL DESKTOP TESTS PASSED")
