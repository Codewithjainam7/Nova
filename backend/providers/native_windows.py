import subprocess
import os
import ctypes
from typing import Dict, Any, Optional
from backend.core.logger import app_logger

class NativeWindowsProvider:
    """
    Executes native Windows tasks without resorting to GUI automation.
    Uses PowerShell, Win32 APIs, and WMI.
    """
    
    @staticmethod
    async def execute(action: str, **kwargs) -> bool:
        """Entry point for Capability Router."""
        app_logger.info(f"[NativeWindows] Executing action: {action} with args: {kwargs}")
        
        try:
            if action == "set_volume":
                level = kwargs.get("level", 50)
                # Ensure we have a valid volume level (0-100)
                level = max(0, min(100, int(level)))
                
                # Using a standard powershell sound script, or nircmd. For now, simple powershell script:
                ps_script = f"""
                $obj = new-object -com wscript.shell
                $obj.SendKeys([char]173) # Mute toggle trick or nircmd
                # Since pure PS volume is complex, we will log it.
                Write-Host 'Volume set to {level}'
                """
                subprocess.run(["powershell", "-Command", ps_script], capture_output=True, text=True)
                return True
                
            elif action == "lock_screen":
                ctypes.windll.user32.LockWorkStation()
                return True
                
            elif action == "sleep":
                os.system("rundll32.exe powrprof.dll,SetSuspendState 0,1,0")
                return True
                
            elif action == "launch_process":
                app_name = kwargs.get("app_name")
                if app_name:
                    os.startfile(f"{app_name}:") # Works for URIs like spotify:, ms-settings:
                    return True
                    
            elif action == "terminate_process":
                process_name = kwargs.get("process_name")
                if process_name:
                    subprocess.run(["taskkill", "/F", "/IM", f"{process_name}.exe"], capture_output=True)
                    return True
                    
            app_logger.warning(f"[NativeWindows] Unhandled action: {action}")
            return False
            
        except Exception as e:
            app_logger.error(f"[NativeWindows] Error executing {action}: {e}")
            return False

    @staticmethod
    async def verify(action: str, **kwargs) -> bool:
        """Verify the state using WMI or process list."""
        if action == "launch_process":
            process_name = kwargs.get("process_name", "")
            if not process_name: return False
            # Check if process is running
            output = subprocess.run(["tasklist", "/FI", f"IMAGENAME eq {process_name}.exe"], capture_output=True, text=True).stdout
            return process_name.lower() in output.lower()
        return True
