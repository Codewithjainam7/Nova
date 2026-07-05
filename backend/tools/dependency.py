from typing import List, Set
from backend.tools.schema import ToolDescriptor
from backend.tools.registry import ToolRegistry
from backend.core.logger import app_logger

class ToolDependencyResolver:
    def __init__(self, registry: ToolRegistry):
        self.registry = registry

    def resolve(self, tool: ToolDescriptor) -> bool:
        """
        Verify that all tool dependencies are registered.
        Returns True if dependencies are satisfied.
        """
        for dep_id in tool.dependencies:
            if not self.registry.get_tool(dep_id):
                app_logger.error(f"Missing dependency {dep_id} for tool {tool.tool_id}")
                return False
        return True
