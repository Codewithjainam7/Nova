# Chapter 29: Extending ADA with Custom Controllers

## Overview
You can extend ADA to control any desktop application by creating a controller in `backend/desktop/controllers/`.

## Step-by-Step Controller Tutorial

### 1. Create Controller File: `notepad_controller.py`
```python
from backend.desktop.controllers.base_controller import AppController
import pyautogui, os, time

class NotepadController(AppController):
    def is_open(self) -> bool:
        # Check if process is running
        return True

    def launch(self):
        os.system("notepad.exe")

    def execute(self, intent: str, entity: str = None) -> bool:
        if intent == "write_text":
            pyautogui.write(entity, interval=0.02)
            return True
        return False
```

### 2. Register in `backend/desktop/controllers/registry.py`
```python
self.register("notepad", NotepadController())
```
