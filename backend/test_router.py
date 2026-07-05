import pytest
from backend.agents.router.schema import AgentDescriptor, AgentHealthStatus, RoutingContext
from backend.agents.router.registry import AgentRegistry, DEFAULT_AGENTS
from backend.agents.router.policy import AgentSelectionPolicy
from backend.agents.router.health import AgentHealthMonitor, AgentAvailabilityTracker
from backend.agents.router.core import AgentRouter

def setup_router() -> AgentRouter:
    registry = AgentRegistry()
    health_monitor = AgentHealthMonitor(registry)
    availability_tracker = AgentAvailabilityTracker(registry)
    policy = AgentSelectionPolicy(registry)
    
    # Register default agents
    for name in DEFAULT_AGENTS:
        priority = 2 if name == "DesktopAgent" else 1
        agent = AgentDescriptor(
            agent_id=name.lower(),
            name=name,
            description=f"{name} description",
            priority=priority,
            health_status=AgentHealthStatus.HEALTHY,
            is_available=True
        )
        registry.register(agent)
        
    return AgentRouter(registry, policy, health_monitor, availability_tracker)

def test_agent_registration():
    router = setup_router()
    agents = router.registry.get_all_agents()
    assert len(agents) == 10
    assert router.registry.get_agent("desktopagent").name == "DesktopAgent"

def test_routing_basic():
    router = setup_router()
    context = RoutingContext(
        task_id="task_1",
        task_description="Open calculator",
        required_agents=["DesktopAgent"]
    )
    result = router.route_task(context)
    assert result.agent_name == "DesktopAgent"
    assert result.health_status == AgentHealthStatus.HEALTHY

def test_fallback_routing():
    router = setup_router()
    
    # Make DesktopAgent busy
    router.availability_tracker.mark_busy("desktopagent")
    
    context = RoutingContext(
        task_id="task_2",
        task_description="Open calculator",
        required_agents=["DesktopAgent", "BrowserAgent"]
    )
    
    result = router.route_task(context)
    # Should fallback to BrowserAgent because DesktopAgent is busy
    assert result.agent_name == "BrowserAgent"
    assert router.metrics.fallback_routes == 1

def test_unhealthy_routing():
    router = setup_router()
    
    # Make DesktopAgent offline
    router.health_monitor.update_health("desktopagent", AgentHealthStatus.OFFLINE)
    
    context = RoutingContext(
        task_id="task_3",
        task_description="Open calculator",
        required_agents=["DesktopAgent"]
    )
    
    # Since only DesktopAgent was requested and it's offline, it should raise error
    with pytest.raises(ValueError):
        router.route_task(context)

if __name__ == "__main__":
    test_agent_registration()
    test_routing_basic()
    test_fallback_routing()
    test_unhealthy_routing()
    print("ALL ROUTER TESTS PASSED")
