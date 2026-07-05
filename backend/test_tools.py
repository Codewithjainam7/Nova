import pytest
from backend.tools.schema import ToolDescriptor, ToolMetadata, ToolCategory, ToolHealthStatus
from backend.tools.core import ToolRegistryManager

def create_mock_tool(tool_id: str, deps=None, perms=None) -> ToolDescriptor:
    return ToolDescriptor(
        tool_id=tool_id,
        name=f"Tool {tool_id}",
        description="Mock tool",
        category=ToolCategory.UTILITY,
        metadata=ToolMetadata(version="1.0.0", author="Test", tags=["mock"]),
        dependencies=deps or [],
        required_permissions=perms or []
    )

def test_tool_registration():
    manager = ToolRegistryManager()
    t1 = create_mock_tool("t1")
    assert manager.register_tool(t1) is True
    assert len(manager.registry.list_tools()) == 1
    assert manager.cache.get_by_category("Utility")[0].tool_id == "t1"

def test_tool_dependency_failure():
    manager = ToolRegistryManager()
    t2 = create_mock_tool("t2", deps=["non_existent_tool"])
    # Registration should fail because dependency is missing
    assert manager.register_tool(t2) is False

def test_tool_permission_failure():
    manager = ToolRegistryManager()
    t3 = create_mock_tool("t3", perms=["root"])
    # Registration should fail because root permission is not granted
    assert manager.register_tool(t3) is False

def test_tool_removal():
    manager = ToolRegistryManager()
    t1 = create_mock_tool("t1")
    manager.register_tool(t1)
    
    manager.remove_tool("t1")
    assert len(manager.registry.list_tools()) == 0
    assert len(manager.cache.get_by_category("Utility")) == 0

if __name__ == "__main__":
    test_tool_registration()
    test_tool_dependency_failure()
    test_tool_permission_failure()
    test_tool_removal()
    print("ALL TOOL REGISTRY TESTS PASSED")
