# Windows Desktop Automation Integration

NOVA utilizes a suite of native python bindings to fully automate the local Windows Desktop environment.

## Libraries
- `pywinauto`: Provides deep hooks into the Windows UI Automation (UIA) API for reliable window traversal, focusing, minimizing, and maximizing based on Regex titles.
- `pyautogui`: Provides robust, screen-absolute coordinate control for mouse movements, clicks, scrolls, and raw keyboard emulation.
- `pyperclip`: Provides a cross-platform API to read and write directly to the host machine's clipboard.
- `psutil`: Exposes running process tables to identify and gracefully terminate underlying application processes (e.g., closing Notepad).
- `pywin32`: Core dependency underlying window handles (HWNDs).

## Architecture
All commands dispatched through the `DesktopManager` are executed via `asyncio.to_thread()`. This is highly critical, as many native OS automation commands are entirely synchronous and blocking. If run directly on the main event loop, they would freeze the FastAPI webserver and disrupt active WebSocket streams.

## Security
The `DesktopPermissionManager` provides hard limits on what can be executed. Operations flagged as `FS_DELETE` or similar destructive file system tasks will strictly require `AUTOMATION` or `DANGEROUS` permissions, stopping rogue AI agents from wiping user data.
