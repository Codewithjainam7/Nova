import asyncio
import pytest
from backend.kernel.schema import KernelRequest, KernelState, KernelConfiguration
from backend.kernel.core import NovaKernel
from backend.kernel.events import KernelEventType

@pytest.mark.asyncio
async def test_kernel_lifecycle():
    kernel = NovaKernel()
    
    # Event tracking
    events_fired = []
    def track_event(payload):
        events_fired.append(payload)
        
    kernel.event_bus.subscribe(KernelEventType.KERNEL_STARTED, track_event)
    
    assert kernel.state_manager.current_state == KernelState.BOOTING
    
    await kernel.startup()
    
    assert kernel.state_manager.current_state == KernelState.IDLE
    assert len(events_fired) == 1
    
    await kernel.shutdown()
    assert kernel.state_manager.current_state == KernelState.SHUTDOWN

@pytest.mark.asyncio
async def test_kernel_pipeline_execution():
    kernel = NovaKernel()
    await kernel.startup()
    
    # Track pipeline states
    states_seen = []
    def track_state(session):
        states_seen.append(session.state)
        
    kernel.event_bus.subscribe(KernelEventType.PLANNING_STARTED, track_state)
    kernel.event_bus.subscribe(KernelEventType.EXECUTION_STARTED, track_state)
    kernel.event_bus.subscribe(KernelEventType.VERIFICATION_STARTED, track_state)
    kernel.event_bus.subscribe(KernelEventType.PROVIDER_INVOKED, track_state)
    
    request = KernelRequest(user_input="Run test")
    response = await kernel.dispatch(request)
    
    assert response.status == KernelState.COMPLETED
    assert KernelState.PLANNING in states_seen
    assert KernelState.EXECUTING in states_seen
    assert KernelState.WAITING in states_seen # Verification state
    assert kernel.metrics.successful_requests == 1
    assert kernel.metrics.active_sessions == 0 # Cleaned up

@pytest.mark.asyncio
async def test_kernel_concurrency_limit():
    # Only allow 1 session at a time
    config = KernelConfiguration(max_concurrent_sessions=1)
    kernel = NovaKernel(config=config)
    await kernel.startup()
    
    # Dispatching two at the exact same time without awaiting the first one immediately
    # We'll artificially mock a long running pipeline to trigger the lock
    
    # Just mock active_sessions to bypass the need for a complex async lock test
    kernel.active_sessions["dummy"] = "dummy"
    
    request = KernelRequest(user_input="Run test 2")
    response = await kernel.dispatch(request)
    
    # Should reject immediately
    assert response.status == KernelState.ERROR
    assert "Max concurrent" in response.error

if __name__ == "__main__":
    asyncio.run(test_kernel_lifecycle())
    asyncio.run(test_kernel_pipeline_execution())
    asyncio.run(test_kernel_concurrency_limit())
    print("ALL KERNEL TESTS PASSED")
