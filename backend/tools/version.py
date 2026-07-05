from backend.tools.schema import ToolDescriptor

class ToolVersionManager:
    @staticmethod
    def is_compatible(tool: ToolDescriptor, required_version: str) -> bool:
        # A simple string match for mock version management.
        # A real system would parse semver (e.g. 1.0.0 >= 1.0.0)
        return tool.metadata.version == required_version
