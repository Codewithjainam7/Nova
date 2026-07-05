import asyncio
import pytest
from backend.browser.schema import BrowserAction, BrowserActionType, BrowserPermissionLevel
from backend.browser.core import BrowserEngine

@pytest.mark.asyncio
async def test_browser_action_execution():
    engine = BrowserEngine()
    
    action = BrowserAction(
        action_type=BrowserActionType.LAUNCH
    )
    
    await engine.perform_action(action)
    assert engine.metrics.total_actions == 1

@pytest.mark.asyncio
async def test_browser_permissions():
    # Set to READ_ONLY
    engine = BrowserEngine(permission_level=BrowserPermissionLevel.READ_ONLY)
    
    action = BrowserAction(
        action_type=BrowserActionType.CLICK,
        payload={"selector": "#submit-btn"}
    )
    
    with pytest.raises(PermissionError):
        await engine.perform_action(action)
        
    assert engine.metrics.failed_actions == 1

@pytest.mark.asyncio
async def test_browser_recovery_on_failure():
    engine = BrowserEngine()
    
    async def failing_dispatch(action):
        raise RuntimeError("Simulated Playwright failure")
        
    engine.manager.dispatcher.dispatch = failing_dispatch
    
    action = BrowserAction(
        action_type=BrowserActionType.NAVIGATE,
        payload={"url": "https://example.com"}
    )
    
    with pytest.raises(RuntimeError):
        await engine.perform_action(action)
        
    assert engine.metrics.failed_actions == 1

if __name__ == "__main__":
    asyncio.run(test_browser_action_execution())
    asyncio.run(test_browser_permissions())
    asyncio.run(test_browser_recovery_on_failure())
    print("ALL BROWSER TESTS PASSED")
