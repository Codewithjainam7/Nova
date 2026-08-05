# Nova: Multi-Platform AI Automation Framework

Nova is a production-grade, multi-layered automation engine designed to empower AI assistants with reliable computer and mobile control capabilities. Unlike traditional macro scripts that rely on brittle screen coordinates, Nova uses an intelligent hierarchy of automation techniques across both **Windows Desktop** and **Android Mobile**. It prefers official APIs and structural UI trees before falling back to OCR or computer vision.

## 🚀 Key Features

*   **Multi-Platform Support:** Seamlessly execute autonomous tasks across desktop environments and connected mobile devices.
*   **Multi-Layered Automation Engine:**
    *   **Desktop Layer (Windows UI Automation):** Deep integration with Microsoft's UI Automation framework to read control hierarchies and interact with native elements without relying on mouse coordinates.
    *   **Mobile Layer (Android/ADB):** Wireless pairing, device management, and mobile UI interaction using Android Debug Bridge (ADB) and Android UIAutomator.
    *   **Future Layers:** Browser Automation (Playwright), OCR (Tesseract/EasyOCR), and Computer Vision (YOLO).
*   **Intelligent Task Planning:** Translates high-level AI goals into structured, executable steps tailored to the target platform.
*   **Robust Verification System:** Never assumes success. Every action (e.g., clicking a button, typing text) is verified against the resulting UI state using smart-polling and timeouts.
*   **Structured Logging:** Granular, JSON-structured event tracking for deep auditing and debugging of AI actions.

## 🏗 Architecture

Nova is designed with strict separation of concerns, ensuring that the AI planner remains decoupled from the underlying execution libraries:

```text
nova/
├── desktop/
│   ├── ui_automation/     # Windows UI tree traversal, window management, and native controls
│   ├── browser/           # Web automation (Playwright/Selenium)
│   └── vision/            # OCR and Object Detection fallback
├── mobile/
│   ├── adb_controller.py  # Wireless ADB pairing and device management
│   ├── uiautomator/       # Android UI tree extraction and interaction
│   └── actions.py         # Mobile-specific primitives (swipe, tap, home, back)
├── core/
│   ├── planner/           # AI task decomposition
│   ├── verifier.py        # Cross-platform state verification 
│   └── logger.py          # Unified telemetry
