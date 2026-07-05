from typing import List, Dict
from backend.tools.schema import ToolDescriptor, ToolHealthStatus
from backend.tools.registry import ToolRegistry
from backend.tools.cache import ToolRegistryCache
from backend.tools.validator import ToolValidator
from backend.tools.dependency import ToolDependencyResolver
from backend.tools.permission import ToolPermissionResolver
from backend.tools.version import ToolVersionManager
from backend.tools.discovery import ToolDiscovery
from backend.tools.health import ToolHealthMonitor
from backend.tools.lifecycle import ToolLifecycleManager
from backend.core.logger import app_logger

class ToolMetrics:
    def __init__(self):
        self.total_tools_registered = 0
        self.failed_validations = 0

class ToolLogger:
    @staticmethod
    def log_registration(tool: ToolDescriptor):
        app_logger.info(f"Successfully fully registered and cached tool {tool.name} ({tool.tool_id})")

class ToolRegistryManager:
    """
    Central Orchestrator for the Tool Registry module.
    NEVER executes tools.
    """
    def __init__(self):
        self.registry = ToolRegistry()
        self.cache = ToolRegistryCache(self.registry)
        self.validator = ToolValidator()
        self.dependency_resolver = ToolDependencyResolver(self.registry)
        self.permission_resolver = ToolPermissionResolver()
        self.health_monitor = ToolHealthMonitor(self.registry)
        self.discovery = ToolDiscovery()
        self.lifecycle = ToolLifecycleManager()
        self.metrics = ToolMetrics()

    def bootstrap(self):
        """Auto-discover and load tools."""
        discovered = self.discovery.discover_tools()
        for t in discovered:
            self.register_tool(t)

    def register_tool(self, tool: ToolDescriptor) -> bool:
        """
        Validates, resolves dependencies, checks permissions, registers, loads resources, and updates cache.
        """
        # Validate
        if not self.validator.validate(tool):
            self.metrics.failed_validations += 1
            return False
            
        # Check permissions
        if not self.permission_resolver.check_permissions(tool):
            self.metrics.failed_validations += 1
            return False
            
        # Check dependencies
        if not self.dependency_resolver.resolve(tool):
            self.metrics.failed_validations += 1
            return False
            
        # Register
        self.registry.register(tool)
        
        # Lifecycle hook
        self.lifecycle.load_tool(tool)
        
        # Update Cache
        self.cache.refresh()
        
        self.metrics.total_tools_registered += 1
        ToolLogger.log_registration(tool)
        return True

    def remove_tool(self, tool_id: str):
        tool = self.registry.get_tool(tool_id)
        if tool:
            self.lifecycle.unload_tool(tool)
            self.registry.remove(tool_id)
            self.cache.refresh()
