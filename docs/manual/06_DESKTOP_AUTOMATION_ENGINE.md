# Chapter 06: Desktop Automation Engine

## Overview
The Desktop Engine (`backend/desktop/core.py`) provides robust, zero-lag local desktop interaction across Windows 10 and 11.

## Multi-Tier Automation Strategy
ADA utilizes a three-tier desktop automation hierarchy:
1. **Tier 1: Protocol & URI Handlers (`ms-settings:`, `spotify:`, `mailto:`)**
   - Fastest, most reliable method (<50ms execution).
   - Direct OS protocol activation without searching screen coordinates.
2. **Tier 2: Windows UIAutomation (UIA) & pywinauto**
   - Inspects the accessibility tree of active windows.
   - Accurately targets buttons, tabs, and input fields by AutomationId and Name.
3. **Tier 3: Coordinate & Vision-Based PyAutoGUI**
   - Low-level keyboard and mouse simulation for non-accessible canvas applications and games.

## Safety & Boundary Controls
- **Fail-Safe Trigger**: Moving the mouse to any screen corner immediately aborts running automation loops.
- **Window Focus Locking**: Ensures the target window is brought to foreground and focused before keystroke injection.
