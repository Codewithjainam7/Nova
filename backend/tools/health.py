from backend.tools.schema import ToolHealthStatus
from backend.tools.registry import ToolRegistry
from backend.core.logger import app_logger

class ToolHealthMonitor:
    def __init__(self, registry: ToolRegistry):
        self.registry = registry

    def update_health(self, tool_id: str, status: ToolHealthStatus):
        tool = self.registry.get_tool(tool_id)
        if tool:
            tool.health_status = status
            app_logger.debug(f"Tool {tool_id} health updated to {status.value}")

    def check_health(self, tool_id: str) -> ToolHealthStatus:
        tool = self.registry.get_tool(tool_id)
        return tool.health_status if tool else ToolHealthStatus.OFFLINE
