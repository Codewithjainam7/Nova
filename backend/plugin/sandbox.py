import asyncio
from typing import Any, Dict
from backend.plugin.schema import PluginManifest, PluginPermissionType, PluginState
from backend.plugin.lifecycle import PluginRegistry
from backend.core.logger import app_logger

class PluginPermissions:
    """Enforces boundary rules for plugin actions."""
    def __init__(self, registry: PluginRegistry):
        self.registry = registry
        
    def check_permission(self, plugin_id: str, required_permission: PluginPermissionType) -> bool:
        manifest = self.registry.get_manifest(plugin_id)
        if not manifest:
            return False
        if required_permission not in manifest.permissions:
            app_logger.warning(f"[PLUGIN PERMISSION] Denied {required_permission.name} for {plugin_id}")
            return False
        return True

class PluginEventBridge:
    """The ONLY channel for a plugin to communicate with the NOVA Kernel."""
    def __init__(self, permissions: PluginPermissions):
        self.permissions = permissions
        
    async def dispatch_to_kernel(self, plugin_id: str, action: str, payload: dict) -> Any:
        app_logger.debug(f"[PLUGIN BRIDGE] Bridging {action} from {plugin_id} to Kernel")
        await asyncio.sleep(0.01) # Simulate IPC/Message Bus
        return {"status": "success", "action": action}

class PluginSandbox:
    """Isolates plugin execution and intercepts system calls."""
    def __init__(self, bridge: PluginEventBridge):
        self.bridge = bridge
        
    async def execute(self, plugin_id: str, action: str, payload: dict) -> Any:
        # In a real environment, this would use WebAssembly, Pyodide, or a separate restricted process.
        # For now, it proxies to the bridge.
        app_logger.debug(f"[PLUGIN SANDBOX] Executing {action} for {plugin_id}")
        return await self.bridge.dispatch_to_kernel(plugin_id, action, payload)

class PluginRuntime:
    """The execution environment for an active plugin."""
    def __init__(self, registry: PluginRegistry, sandbox: PluginSandbox):
        self.registry = registry
        self.sandbox = sandbox
        
    async def invoke(self, plugin_id: str, action: str, payload: Dict[str, Any]) -> Any:
        state = self.registry.get_state(plugin_id)
        if state != PluginState.ENABLED:
            raise RuntimeError(f"Cannot invoke plugin {plugin_id}: State is {state.name}")
            
        return await self.sandbox.execute(plugin_id, action, payload)
