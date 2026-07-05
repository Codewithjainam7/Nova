import asyncio
import pytest
from backend.plugin.schema import PluginState, PluginPermissionType
from backend.plugin.core import PluginSystem

@pytest.mark.asyncio
async def test_plugin_initialization_and_lifecycle():
    system = PluginSystem()
    system.config.allow_unsigned = True
    
    # 1. Initialize (Discover and Load)
    await system.initialize()
    
    assert system.metrics.total_plugins_loaded == 1
    state = system.manager.registry.get_state("com.nova.mock")
    assert state == PluginState.LOADED
    
    # 2. Enable
    await system.enable_plugin("com.nova.mock")
    state = system.manager.registry.get_state("com.nova.mock")
    assert state == PluginState.ENABLED
    
    # 3. Disable
    await system.disable_plugin("com.nova.mock")
    state = system.manager.registry.get_state("com.nova.mock")
    assert state == PluginState.DISABLED

@pytest.mark.asyncio
async def test_plugin_invocation_and_sandbox():
    system = PluginSystem()
    system.config.allow_unsigned = True
    await system.initialize()
    
    # Cannot invoke if not enabled
    with pytest.raises(RuntimeError):
        await system.invoke_plugin("com.nova.mock", "DO_ACTION")
        
    # Enable and invoke
    await system.enable_plugin("com.nova.mock")
    result = await system.invoke_plugin("com.nova.mock", "DO_ACTION")
    
    assert result["status"] == "success"
    assert result["action"] == "DO_ACTION"
    assert system.metrics.total_events_bridged == 1

@pytest.mark.asyncio
async def test_plugin_permission_denial():
    system = PluginSystem()
    system.config.allow_unsigned = True
    await system.initialize()
    
    # Check permission that the mock plugin doesn't have (DANGEROUS)
    has_perm = system.manager.permissions.check_permission("com.nova.mock", PluginPermissionType.DANGEROUS)
    assert has_perm is False

if __name__ == "__main__":
    asyncio.run(test_plugin_initialization_and_lifecycle())
    asyncio.run(test_plugin_invocation_and_sandbox())
    asyncio.run(test_plugin_permission_denial())
    print("ALL PLUGIN TESTS PASSED")
