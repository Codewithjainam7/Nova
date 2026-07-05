import time
import asyncio
from typing import Any, Dict
from backend.plugin.schema import PluginConfiguration, PluginMetrics, PluginState
from backend.plugin.lifecycle import PluginRegistry, PluginLoader, PluginLifecycle
from backend.plugin.sandbox import PluginPermissions, PluginEventBridge, PluginSandbox, PluginRuntime
from backend.core.logger import app_logger

class PluginLogger:
    @staticmethod
    def log_invocation(plugin_id: str, action: str, status: str):
        app_logger.info(f"[PLUGIN INVOCATION - {status}] {plugin_id} -> {action}")

class PluginManager:
    """Dependency Injection Container for the Plugin subsystem."""
    def __init__(self, config: PluginConfiguration):
        self.config = config
        self.registry = PluginRegistry()
        self.loader = PluginLoader(self.config, self.registry)
        self.lifecycle = PluginLifecycle(self.loader, self.registry)
        self.permissions = PluginPermissions(self.registry)
        self.bridge = PluginEventBridge(self.permissions)
        self.sandbox = PluginSandbox(self.bridge)
        self.runtime = PluginRuntime(self.registry, self.sandbox)

class PluginSystem:
    """Central entrypoint for the NOVA Plugin subsystem."""
    def __init__(self):
        self.config = PluginConfiguration()
        self.metrics = PluginMetrics()
        self.manager = PluginManager(self.config)

    async def initialize(self):
        """Discovers, loads, and validates all plugins on startup."""
        start = time.time()
        manifests = await self.manager.loader.discover()
        
        for manifest in manifests:
            success = await self.manager.lifecycle.load(manifest.plugin_id)
            if success:
                self.metrics.total_plugins_loaded += 1
                
        elapsed = (time.time() - start) * 1000
        self._update_metric("avg_load_latency_ms", elapsed)

    async def enable_plugin(self, plugin_id: str):
        await self.manager.lifecycle.enable(plugin_id)
        
    async def disable_plugin(self, plugin_id: str):
        await self.manager.lifecycle.disable(plugin_id)

    async def invoke_plugin(self, plugin_id: str, action: str, payload: Dict[str, Any] = None) -> Any:
        """Executes an action within the plugin's sandboxed runtime."""
        payload = payload or {}
        PluginLogger.log_invocation(plugin_id, action, "START")
        
        try:
            result = await self.manager.runtime.invoke(plugin_id, action, payload)
            PluginLogger.log_invocation(plugin_id, action, "SUCCESS")
            self.metrics.total_events_bridged += 1
            return result
        except Exception as e:
            PluginLogger.log_invocation(plugin_id, action, f"FAILED: {str(e)}")
            raise

    def _update_metric(self, attr: str, elapsed: float):
        n = getattr(self.metrics, "total_plugins_loaded", 1)
        if n > 0:
            current = getattr(self.metrics, attr)
            new_val = ((current * (n - 1)) + elapsed) / n
            setattr(self.metrics, attr, new_val)
