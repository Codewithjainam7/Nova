# Desktop Implementation Architecture

NOVA has successfully replaced the mock OS abstractions with a native Windows Desktop Automation layer.

## Component Flow

```mermaid
graph TD
    User[User/Planner Request] --> Engine[Desktop Engine]
    Engine --> Permissions[Desktop Permission Manager]
    Permissions -->|Approved| Dispatcher[Desktop Action Dispatcher]
    Permissions -->|Denied| Error
    
    Dispatcher --> Windows[Windows Adapters]
    
    Windows -->|Application Mgmt| Psutil[psutil / os]
    Windows -->|Window Focus| PyWinAuto[pywinauto UIA]
    Windows -->|Mouse/Keyboard| PyAutoGUI[pyautogui]
    Windows -->|Clipboard| Pyperclip[pyperclip]
    Windows -->|Filesystem| Shutil[os / shutil]
    
    Windows -->|Error| Recovery[Desktop Recovery Manager]
    Recovery -->|Retry| Windows
```

## Security & Threading
1. **Thread Pooling**: The `asyncio.to_thread` executor is heavily leveraged across all adapter endpoints. Because `pyautogui` and `pywinauto` perform blocking system calls that sleep/wait for UI animations, wrapping them in thread pools prevents the primary `uvicorn` event loop from stalling.
2. **Permission Gatekeeping**: Every action passes through `DesktopPermissionManager.check()`. If the AI attempts to mutate state (e.g. `FILE_DELETE`) without explicitly being assigned an `AUTOMATION` or `DANGEROUS` role, the operation throws a hard `PermissionError` which cascades up to the kernel as a failed execution result.
