import asyncio
from typing import Dict, Optional, List
from backend.plugin.schema import PluginManifest, PluginState, PluginConfiguration
from backend.core.logger import app_logger

class PluginRegistry:
    """Maintains the active state of all plugins in the system."""
    def __init__(self):
        self._manifests: Dict[str, PluginManifest] = {}
        self._states: Dict[str, PluginState] = {}
        
    def register(self, manifest: PluginManifest):
        self._manifests[manifest.plugin_id] = manifest
        self._states[manifest.plugin_id] = PluginState.UNLOADED
        
    def update_state(self, plugin_id: str, state: PluginState):
        if plugin_id in self._states:
            self._states[plugin_id] = state
            
    def get_manifest(self, plugin_id: str) -> Optional[PluginManifest]:
        return self._manifests.get(plugin_id)
        
    def get_state(self, plugin_id: str) -> Optional[PluginState]:
        return self._states.get(plugin_id)
        
    def get_all(self) -> List[PluginManifest]:
        return list(self._manifests.values())

class PluginLoader:
    """Responsible for discovering and reading plugin manifests."""
    def __init__(self, config: PluginConfiguration, registry: PluginRegistry):
        self.config = config
        self.registry = registry
        
    async def discover(self) -> List[PluginManifest]:
        app_logger.debug(f"[PLUGIN LOADER] Discovering plugins in {self.config.plugin_directory}")
        await asyncio.sleep(0.01) # Simulate file IO
        
        # Mock discovery for testing
        manifest = PluginManifest(
            plugin_id="com.nova.mock",
            name="Mock Plugin",
            version="1.0.0",
            author="NOVA Team",
            description="A mock plugin for testing",
            required_runtime_version="1.0.0",
            required_api_version="1.0.0"
        )
        self.registry.register(manifest)
        return [manifest]
        
    async def validate(self, manifest: PluginManifest) -> bool:
        app_logger.debug(f"[PLUGIN LOADER] Validating {manifest.plugin_id}")
        if self.config.strict_sandbox and not self.config.allow_unsigned and not manifest.digital_signature:
            app_logger.warning(f"[PLUGIN LOADER] {manifest.plugin_id} failed validation: Missing digital signature.")
            return False
        return True

class PluginLifecycle:
    """Manages the state transitions of a plugin."""
    def __init__(self, loader: PluginLoader, registry: PluginRegistry):
        self.loader = loader
        self.registry = registry
        
    async def load(self, plugin_id: str) -> bool:
        self.registry.update_state(plugin_id, PluginState.LOADING)
        manifest = self.registry.get_manifest(plugin_id)
        
        if not manifest:
            self.registry.update_state(plugin_id, PluginState.ERROR)
            return False
            
        is_valid = await self.loader.validate(manifest)
        if not is_valid:
            self.registry.update_state(plugin_id, PluginState.ERROR)
            return False
            
        app_logger.info(f"[PLUGIN LIFECYCLE] Loaded {plugin_id}")
        self.registry.update_state(plugin_id, PluginState.LOADED)
        return True
        
    async def enable(self, plugin_id: str):
        if self.registry.get_state(plugin_id) == PluginState.LOADED:
            app_logger.info(f"[PLUGIN LIFECYCLE] Enabled {plugin_id}")
            self.registry.update_state(plugin_id, PluginState.ENABLED)
            
    async def disable(self, plugin_id: str):
        if self.registry.get_state(plugin_id) == PluginState.ENABLED:
            app_logger.info(f"[PLUGIN LIFECYCLE] Disabled {plugin_id}")
            self.registry.update_state(plugin_id, PluginState.DISABLED)
