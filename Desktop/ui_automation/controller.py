from .window_manager import WindowManager
from .element_finder import ElementFinder
from .action_executor import ActionExecutor
from .verifier import Verifier
import uiautomation as auto

class UIAutomationController:
    """Facade for the Windows UI Automation Engine."""
    
    def __init__(self):
        self.windows = WindowManager()
        self.finder = ElementFinder()
        self.actions = ActionExecutor()
        self.verifier = Verifier()
        
    # --- Window Management Facade ---
    def find_window(self, **kwargs) -> auto.WindowControl:
        return self.windows.find_window(**kwargs)
        
    def activate_window(self, window: auto.WindowControl) -> bool:
        return self.windows.activate_window(window)
        
    def close_window(self, window: auto.WindowControl) -> bool:
        return self.windows.close_window(window)
        
    # --- Element Discovery Facade ---
    def find_element(self, parent: auto.Control, **kwargs) -> auto.Control:
        return self.finder.find_element(parent, **kwargs)
        
    # --- Actions Facade ---
    def click(self, element: auto.Control, **kwargs) -> bool:
        return self.actions.click(element, **kwargs)
        
    def type_text(self, element: auto.Control, text: str, **kwargs) -> bool:
        return self.actions.type_text(element, text, **kwargs)
        
    def read_text(self, element: auto.Control) -> str:
        return self.actions.read_text(element)
        
    def expand(self, element: auto.Control) -> bool:
        return self.actions.expand(element)
        
    def toggle(self, element: auto.Control) -> bool:
        return self.actions.toggle(element)

    # --- Verification Facade ---
    def wait_for_element(self, parent: auto.Control, timeout: float = 5.0, **kwargs) -> auto.Control:
        resolver = lambda: self.finder.find_element(parent, **kwargs)
        return self.verifier.wait_until_exists(resolver, timeout)
