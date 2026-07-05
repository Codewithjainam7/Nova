from typing import List, Dict, Optional
from backend.tools.schema import ToolDescriptor
from backend.tools.registry import ToolRegistry

class ToolRegistryCache:
    """In-memory cache for fast tool lookups."""
    def __init__(self, registry: ToolRegistry):
        self.registry = registry
        self._category_index: Dict[str, List[str]] = {}
        
    def refresh(self):
        self._category_index.clear()
        for tool in self.registry.list_tools():
            cat = tool.category.value
            if cat not in self._category_index:
                self._category_index[cat] = []
            self._category_index[cat].append(tool.tool_id)
            
    def get_by_category(self, category: str) -> List[ToolDescriptor]:
        tool_ids = self._category_index.get(category, [])
        tools = []
        for tid in tool_ids:
            t = self.registry.get_tool(tid)
            if t:
                tools.append(t)
        return tools
