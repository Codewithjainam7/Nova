from dataclasses import dataclass
from typing import Any, Optional, Dict

@dataclass
class UIElementInfo:
    """Represents a simplified model of a UI Element for logging/serialization."""
    name: str
    control_type: str
    class_name: str
    automation_id: str
    is_enabled: bool
    is_visible: bool
    bounding_rectangle: Optional[Dict[str, int]] = None

    @classmethod
    def from_uiautomation_control(cls, control: Any) -> 'UIElementInfo':
        """Creates a UIElementInfo from a uiautomation Control."""
        rect = None
        try:
            r = control.BoundingRectangle
            rect = {"left": r.left, "top": r.top, "right": r.right, "bottom": r.bottom}
        except:
            pass

        return cls(
            name=control.Name,
            control_type=control.ControlTypeName,
            class_name=control.ClassName,
            automation_id=control.AutomationId,
            is_enabled=control.IsEnabled,
            is_visible=not control.IsOffscreen,
            bounding_rectangle=rect
        )

@dataclass
class WindowInfo:
    """Represents a simplified model of a top-level window."""
    handle: int
    title: str
    process_id: int
    class_name: str
    is_active: bool
    
    @classmethod
    def from_uiautomation_window(cls, window: Any, is_active: bool = False) -> 'WindowInfo':
        """Creates a WindowInfo from a uiautomation WindowControl."""
        return cls(
            handle=window.NativeWindowHandle,
            title=window.Name,
            process_id=window.ProcessId,
            class_name=window.ClassName,
            is_active=is_active
        )
