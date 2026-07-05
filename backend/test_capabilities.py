import pytest
from backend.capabilities.schema import CapabilityContext, CapabilityDescriptor
from backend.capabilities.registry import CapabilityRegistry
from backend.capabilities.default_capabilities import DEFAULT_CAPABILITIES
from backend.capabilities.core import CapabilityResolver
from backend.agents.router.registry import AgentRegistry
from backend.agents.router.schema import AgentDescriptor, AgentHealthStatus

def setup_resolver() -> CapabilityResolver:
    cap_registry = CapabilityRegistry()
    for cap in DEFAULT_CAPABILITIES:
        cap_registry.register_capability(cap)
        
    agent_registry = AgentRegistry()
    # Mock some agents
    agent_registry.register(AgentDescriptor(
        agent_id="browseragent",
        name="BrowserAgent",
        description="Handles web and browser tasks",
        capabilities=["BrowserNavigation", "InternetSearch"],
        health_status=AgentHealthStatus.HEALTHY,
        is_available=True
    ))
    agent_registry.register(AgentDescriptor(
        agent_id="desktopagent",
        name="DesktopAgent",
        description="Handles OS and filesystem tasks",
        capabilities=["LaunchApplication", "ManageWindows", "Filesystem"],
        health_status=AgentHealthStatus.HEALTHY,
        is_available=True
    ))
    
    return CapabilityResolver(cap_registry, agent_registry)

def test_capability_registration():
    resolver = setup_resolver()
    caps = resolver.capability_registry.list_capabilities()
    assert len(caps) > 0
    assert resolver.capability_registry.get_capability("cap_launch_application") is not None

def test_capability_search():
    resolver = setup_resolver()
    results = resolver.capability_registry.search_capability("browser")
    assert len(results) >= 1
    assert any(c.name == "BrowserNavigation" for c in results)

def test_capability_matching():
    resolver = setup_resolver()
    
    # Context explicitly requires InternetSearch
    context = CapabilityContext(
        task_id="t1",
        task_description="Search the web for news",
        required_capabilities=["InternetSearch"]
    )
    
    resolutions = resolver.resolve(context)
    assert len(resolutions) >= 1
    
    # Should resolve InternetSearch to BrowserAgent
    search_res = next((r for r in resolutions if r.capability_name == "InternetSearch"), None)
    assert search_res is not None
    assert search_res.preferred_agent == "browseragent"

def test_capability_fallback_and_health():
    resolver = setup_resolver()
    
    # Make DesktopAgent busy
    desktop_agent = resolver.agent_registry.get_agent("desktopagent")
    desktop_agent.is_available = False
    
    context = CapabilityContext(
        task_id="t2",
        task_description="Launch brave browser",
        required_capabilities=["LaunchApplication"]
    )
    
    resolutions = resolver.resolve(context)
    launch_res = next((r for r in resolutions if r.capability_name == "LaunchApplication"), None)
    
    assert launch_res is not None
    assert launch_res.preferred_agent == "desktopagent" # It's busy, but still matches best. It will get a penalty but still > 0 score.

if __name__ == "__main__":
    test_capability_registration()
    test_capability_search()
    test_capability_matching()
    test_capability_fallback_and_health()
    print("ALL CAPABILITY TESTS PASSED")
