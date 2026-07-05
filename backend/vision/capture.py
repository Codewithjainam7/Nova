import mss
import mss.tools
import pygetwindow as gw
from typing import Optional, Dict
from backend.core.logger import app_logger

class ScreenCaptureManager:
    def capture_full_screen(self, monitor_index: int = 1) -> bytes:
        app_logger.debug(f"Capturing full screen (Monitor {monitor_index})")
        with mss.mss() as sct:
            if monitor_index > len(sct.monitors) - 1:
                app_logger.warning(f"Monitor {monitor_index} out of bounds, defaulting to monitor 1")
                monitor_index = 1
            monitor = sct.monitors[monitor_index]
            sct_img = sct.grab(monitor)
            return mss.tools.to_png(sct_img.rgb, sct_img.size)

class RegionCaptureManager:
    def capture_region(self, x: int, y: int, width: int, height: int) -> bytes:
        app_logger.debug(f"Capturing region {width}x{height} at {x},{y}")
        with mss.mss() as sct:
            monitor = {"top": y, "left": x, "width": width, "height": height}
            sct_img = sct.grab(monitor)
            return mss.tools.to_png(sct_img.rgb, sct_img.size)

class WindowCaptureManager:
    def capture_window(self, window_title: str) -> Optional[bytes]:
        app_logger.debug(f"Capturing window '{window_title}'")
        windows = gw.getWindowsWithTitle(window_title)
        if not windows:
            app_logger.error(f"No window found with title '{window_title}'")
            return None
            
        win = windows[0]
        if win.isMinimized:
            app_logger.warning(f"Window '{window_title}' is minimized.")
            
        with mss.mss() as sct:
            monitor = {
                "top": win.top,
                "left": win.left,
                "width": win.width,
                "height": win.height
            }
            sct_img = sct.grab(monitor)
            return mss.tools.to_png(sct_img.rgb, sct_img.size)
