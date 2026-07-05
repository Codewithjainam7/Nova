from backend.tools.schema import ToolDescriptor
from backend.core.logger import app_logger

class ToolValidator:
    @staticmethod
    def validate(tool: ToolDescriptor) -> bool:
        if not tool.tool_id or not tool.name:
            app_logger.error(f"Validation failed: Tool missing ID or name")
            return False
        if not tool.metadata or not tool.metadata.version:
            app_logger.error(f"Validation failed: Tool {tool.tool_id} missing version")
            return False
        return True
