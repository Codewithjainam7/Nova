from typing import Dict, List, Optional
from backend.tools.schema import ToolDescriptor
from backend.core.logger import app_logger

class ToolRegistry:
    def __init__(self):
        self._tools: Dict[str, ToolDescriptor] = {}

    def register(self, tool: ToolDescriptor):
        self._tools[tool.tool_id] = tool
        app_logger.info(f"Registered tool: {tool.tool_id}")

    def remove(self, tool_id: str):
        if tool_id in self._tools:
            del self._tools[tool_id]
            app_logger.info(f"Removed tool: {tool_id}")

    def update(self, tool: ToolDescriptor):
        if tool.tool_id in self._tools:
            self._tools[tool.tool_id] = tool
            app_logger.info(f"Updated tool: {tool.tool_id}")
        else:
            self.register(tool)

    def get_tool(self, tool_id: str) -> Optional[ToolDescriptor]:
        return self._tools.get(tool_id)

    def list_tools(self) -> List[ToolDescriptor]:
        return list(self._tools.values())

    def search_tools(self, keyword: str) -> List[ToolDescriptor]:
        keyword = keyword.lower()
        results = []
        for tool in self._tools.values():
            if keyword in tool.name.lower() or keyword in tool.description.lower() or any(keyword in t.lower() for t in tool.metadata.tags):
                results.append(tool)
        return results
