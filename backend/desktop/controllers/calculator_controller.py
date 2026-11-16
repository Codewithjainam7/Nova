import time
import os
import re
import ctypes
from typing import Optional
from backend.desktop.controllers.base_controller import AppController
from backend.core.logger import app_logger
import uiautomation as auto

def _ensure_desktop():
    try:
        user32 = ctypes.windll.user32
        h_default = user32.OpenDesktopW("Default", 0, False, 0x01FF)
        if h_default:
            user32.SetThreadDesktop(h_default)
    except Exception:
        pass

class CalculatorController(AppController):
    """
    Dedicated controller for Windows Calculator.
    Handles autonomous calculations, keyboard/button interactions, and result verification via UIA.
    """

    def __init__(self):
        self.last_result: Optional[str] = None

    def _get_calc_window(self) -> Optional[auto.WindowControl]:
        _ensure_desktop()
        root = auto.GetRootControl()
        for child in root.GetChildren():
            try:
                name = (child.Name or "").lower()
                if "calculator" in name:
                    return child
            except Exception:
                continue
        return None

    def is_open(self) -> bool:
        return self._get_calc_window() is not None

    def launch(self):
        _ensure_desktop()
        app_logger.info("Launching Windows Calculator via URI scheme...")
        try:
            os.startfile("calculator:")
        except Exception as e:
            app_logger.warning(f"Failed to startfile 'calculator:': {e}. Falling back to calc.exe.")
            try:
                os.startfile("calc.exe")
            except Exception as e2:
                app_logger.error(f"Failed to launch Calculator: {e2}")

    def wait_ready(self, timeout: int = 10) -> bool:
        _ensure_desktop()
        start = time.time()
        while time.time() - start < timeout:
            win = self._get_calc_window()
            if win:
                res = win.TextControl(searchDepth=10, AutomationId="CalculatorResults")
                if res.Exists(0, 0):
                    return True
            time.sleep(0.5)
        return False

    def get_result(self) -> str:
        _ensure_desktop()
        win = self._get_calc_window()
        if not win:
            return ""
        res_ctrl = win.TextControl(searchDepth=10, AutomationId="CalculatorResults")
        if res_ctrl.Exists(1, 1):
            raw = res_ctrl.Name or ""
            cleaned = re.sub(r"^Display\s+is\s+", "", raw, flags=re.IGNORECASE).strip()
            self.last_result = cleaned
            return cleaned
        return ""

    def calculate_expression(self, expr: str) -> str:
        """
        Executes an arithmetic expression directly in the Calculator UI.
        e.g., '25 * 4', '125 * 8', '150 + 75 - 20', '500 / 5'
        """
        _ensure_desktop()
        win = self._get_calc_window()
        if not win:
            raise RuntimeError("Calculator window is not open.")
            
        win.SetActive()
        time.sleep(0.2)
        
        # Reset state (Escape)
        win.SendKeys("{Esc}")
        time.sleep(0.2)
        
        # Format expression
        expr = expr.replace(" ", "").lower()
        if not expr.endswith("="):
            expr += "="
            
        app_logger.info(f"CalculatorController: Sending expression '{expr}' to Calculator")
        win.SendKeys(expr)
        time.sleep(0.4)
        
        result = self.get_result()
        app_logger.info(f"CalculatorController: Final computation result: {result}")
        return result

    def execute(self, intent: str, entity: Optional[str]) -> bool:
        _ensure_desktop()
        win = self._get_calc_window()
        if not win:
            if not self.wait_ready(timeout=3):
                return False
            win = self._get_calc_window()

        intent = intent.lower().strip()
        
        if intent in ["open_app", "launch"]:
            if win:
                win.SetActive()
            return True
            
        elif intent in ["calculate", "compute", "math"] and entity:
            res = self.calculate_expression(entity)
            self.last_result = res
            return True
            
        elif intent == "get_result":
            res = self.get_result()
            self.last_result = res
            return True
            
        elif intent == "close_app":
            if win:
                win.SendKeys("{Alt}{F4}")
                return True
                
        return False
