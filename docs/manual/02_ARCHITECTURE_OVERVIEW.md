# Chapter 02: System Architecture Overview

## Architectural Philosophy
ADA is engineered around a decoupled, asynchronous micro-kernel pattern. Unlike conventional conversational chatbots that merely output text, ADA operates as an **action-oriented autonomous executive**. Every user query or voice utterance is translated into executable intent DAGs (Directed Acyclic Graphs), verified for safety, and dispatched to native OS controllers.

## Core Architectural Layers

```
+-------------------------------------------------------------+
|                  Holographic Frontend (React/Three.js)      |
|   - 3D Neural Brain Canvas        - Voice Orb & Waveforms   |
|   - Real-time Telemetry HUD       - Dynamic Island Overlay  |
+-------------------------------------------------------------+
                              | WebSocket (/ws/chat, /ws/events)
+-------------------------------------------------------------+
|                   ADA Kernel Subsystem                      |
|   - State Machine (BOOT, IDLE, PLANNING, EXECUTING)         |
|   - Dependency Injection Container                          |
|   - Action Sequencer & Fault Recovery Engine                |
+-------------------------------------------------------------+
         |                       |                     |
+-----------------+     +-----------------+     +-------------+
| Cognitive Core  |     | Capability Core |     | Memory Core |
| - Gemini 2.0/Pro|     | - Router        |     | - ChromaDB  |
| - Groq Whisper  |     | - Permissions   |     | - SQLite    |
| - Hierarchical  |     | - Rate Limiter  |     | - Embedder  |
|   Planner       |     | - Intent Match  |     |             |
+-----------------+     +-----------------+     +-------------+
         |                       |
+-------------------------------------------------------------+
|                     Execution Engines                       |
|   - DesktopEngine (Win32, UIA, PyAutoGUI, Windows URIs)     |
|   - BrowserEngine (Playwright Headless/Headed)              |
|   - DeviceEngine (Auto-ADB Wireless Android Controller)     |
+-------------------------------------------------------------+
```

## Subsystem Lifecycle
1. **Booting Phase**: Environment variables and encrypted credential stores are decrypted.
2. **DI Bootstrap**: Singletons for `AIProviderManager`, `PlannerCore`, `DesktopEngine`, `BrowserEngine`, and `MemoryEngine` are instantiated.
3. **Hardware & Device Probing**: ADB scans the local subnet for wireless Android devices; Audio subsystem verifies microphone sample rates.
4. **Active Runtime**: EventBus streams operational metrics to the WebGL HUD while awaiting user voice or text directives.
