import time
import uiautomation as auto
from .exceptions import ActionTimeoutError
from .logger import UILogger

class Verifier:
    """Verifies UI states and handles intelligent waiting."""
    
    def wait_until_exists(self, element_resolver, timeout: float = 5.0) -> auto.Control:
        """Waits until a resolver function returns a valid element."""
        start = time.time()
        while (time.time() - start) < timeout:
            try:
                el = element_resolver()
                if el and el.Exists(0, 0):
                    return el
            except Exception:
                pass
            time.sleep(0.5)
            
        raise ActionTimeoutError(f"Element did not exist within {timeout}s")
        
    def wait_until_vanishes(self, element: auto.Control, timeout: float = 5.0) -> bool:
        """Waits until an element is no longer in the UI tree."""
        start = time.time()
        while (time.time() - start) < timeout:
            if not element.Exists(0, 0):
                return True
            time.sleep(0.5)
            
        raise ActionTimeoutError(f"Element did not vanish within {timeout}s")

    def verify_text_changed(self, element: auto.Control, expected_text: str, timeout: float = 3.0) -> bool:
        """Verifies the text of an element matches the expected value."""
        start = time.time()
        while (time.time() - start) < timeout:
            try:
                # Try getting pattern value or name
                try:
                    val = element.GetValuePattern().Value
                except Exception:
                    val = element.Name
                    
                if val == expected_text:
                    return True
            except Exception:
                pass
            time.sleep(0.5)
            
        raise ActionTimeoutError(f"Text did not match expected value within {timeout}s")
