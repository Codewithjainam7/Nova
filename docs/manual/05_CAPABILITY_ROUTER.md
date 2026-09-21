# Chapter 05: Capability Router & Tool Dispatch

## Overview
The Capability Router (`backend/kernel/capability_router.py`) acts as the dispatch hub that bridges abstract planner tasks to concrete system engines.

## Routing Logic
When a task arrives at the Capability Router:
1. **Tool Evaluation**: Inspects `task.required_tools`.
2. **Desktop Routing**:
   - If `desktop` is required, checks `task.action_metadata`.
   - Delegates to `AppActionRouter` for application-specific controllers (Spotify, Settings, Notepad).
   - Falls back to `DesktopEngine` for general Windows UIAutomation and PyAutoGUI actions.
3. **Browser Routing**:
   - Dispatches URL navigation, DOM interactions, and web scraping to `BrowserEngine`.
4. **Device Routing**:
   - Dispatches mobile commands (e.g., "open WhatsApp on my phone") to `DeviceEngine` via ADB.
5. **Native Windows Provider**:
   - Handles low-level OS operations (volume adjustment, screen lock, sleep mode) using direct Win32 and PowerShell APIs.

## Execution Isolation
Every task execution is wrapped in try-catch error boundaries. If an action fails, the router reports detailed failure telemetry to the kernel for autonomous recovery without crashing the host application.
