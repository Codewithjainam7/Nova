from backend.tools.schema import ToolDescriptor
from backend.core.logger import app_logger

class ToolLifecycleManager:
    """Manages dynamic loading and unloading of tool plugins."""
    @staticmethod
    def load_tool(tool: ToolDescriptor):
        app_logger.info(f"Loaded tool resources for {tool.tool_id}")

    @staticmethod
    def unload_tool(tool: ToolDescriptor):
        app_logger.info(f"Unloaded tool resources for {tool.tool_id}")
