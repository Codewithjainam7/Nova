import uiautomation as auto
import time
from .exceptions import ElementNotEnabledError, ElementNotVisibleError, UIAutomationError
from .logger import UILogger

class ActionExecutor:
    """Executes actions on UI elements using UI Automation Patterns."""
    
    def _check_interactable(self, element: auto.Control):
        if not element.Exists(0, 0):
            raise UIAutomationError("Element does not exist.")
        if not element.IsEnabled:
            raise ElementNotEnabledError("Element is not enabled.")
        if element.IsOffscreen:
            # sometimes elements are offscreen but still interactable via patterns
            pass
            
    def click(self, element: auto.Control, double_click: bool = False, right_click: bool = False) -> bool:
        start_time = time.time()
        try:
            self._check_interactable(element)
            
            # Try Invoke pattern first if just a normal click
            if not double_click and not right_click:
                try:
                    element.GetInvokePattern().Invoke()
                    UILogger.log_action("Invoke", element.Name, True, int((time.time()-start_time)*1000))
                    return True
                except Exception:
                    pass
            
            # Fallback to physical click
            if double_click:
                element.DoubleClick(simulateMove=False)
            elif right_click:
                element.RightClick(simulateMove=False)
            else:
                element.Click(simulateMove=False)
                
            UILogger.log_action("Click", element.Name, True, int((time.time()-start_time)*1000))
            return True
        except Exception as e:
            UILogger.log_action("Click", getattr(element, 'Name', 'Unknown'), False, int((time.time()-start_time)*1000), e)
            raise e

    def type_text(self, element: auto.Control, text: str, append: bool = False) -> bool:
        start_time = time.time()
        try:
            self._check_interactable(element)
            
            # Try Value pattern first
            try:
                pattern = element.GetValuePattern()
                if append:
                    current = pattern.Value
                    pattern.SetValue(current + text)
                else:
                    pattern.SetValue(text)
                UILogger.log_action("SetValue", element.Name, True, int((time.time()-start_time)*1000))
                return True
            except Exception:
                pass
                
            # Fallback to physical keyboard
            element.SetFocus()
            time.sleep(0.1)
            if not append:
                auto.SendKeys('{Ctrl}a{Delete}')
            auto.SendKeys(text)
            
            UILogger.log_action("TypeText", element.Name, True, int((time.time()-start_time)*1000))
            return True
        except Exception as e:
            UILogger.log_action("TypeText", getattr(element, 'Name', 'Unknown'), False, int((time.time()-start_time)*1000), e)
            raise e
            
    def read_text(self, element: auto.Control) -> str:
        """Reads text from an element using patterns or properties."""
        try:
            self._check_interactable(element)
            try:
                return element.GetValuePattern().Value
            except Exception:
                pass
            return element.Name
        except Exception as e:
            UILogger.error("Failed to read text", exc_info=True)
            raise e
            
    def expand(self, element: auto.Control) -> bool:
        try:
            self._check_interactable(element)
            element.GetExpandCollapsePattern().Expand()
            return True
        except Exception as e:
            raise UIAutomationError(f"Cannot expand element: {e}")
            
    def collapse(self, element: auto.Control) -> bool:
        try:
            self._check_interactable(element)
            element.GetExpandCollapsePattern().Collapse()
            return True
        except Exception as e:
            raise UIAutomationError(f"Cannot collapse element: {e}")
            
    def toggle(self, element: auto.Control) -> bool:
        try:
            self._check_interactable(element)
            element.GetTogglePattern().Toggle()
            return True
        except Exception as e:
            raise UIAutomationError(f"Cannot toggle element: {e}")
