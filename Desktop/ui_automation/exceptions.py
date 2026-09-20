class UIAutomationError(Exception):
    """Base class for all UI Automation exceptions."""
    pass

class WindowNotFoundError(UIAutomationError):
    """Raised when a specified window cannot be found."""
    pass

class MultipleWindowsFoundError(UIAutomationError):
    """Raised when multiple windows match the search criteria but a single target was expected."""
    pass

class ElementNotFoundError(UIAutomationError):
    """Raised when a specific UI element cannot be found."""
    pass

class ElementNotEnabledError(UIAutomationError):
    """Raised when an action is attempted on a disabled element."""
    pass

class ElementNotVisibleError(UIAutomationError):
    """Raised when an action is attempted on a hidden element."""
    pass

class ActionTimeoutError(UIAutomationError):
    """Raised when a wait condition or action times out."""
    pass

class AccessDeniedError(UIAutomationError):
    """Raised when Nova lacks permissions to interact with a window (e.g., elevated processes)."""
    pass
