# ADA // Mark VII Autonomous AI Operating System

<div align="center">

```
   █████╗ ██████╗  █████╗     ███╗   ███╗ █████╗ ██████╗ ██╗  ██╗    ██╗   ██╗██╗██╗
  ██╔══██╗██╔══██╗██╔══██╗    ████╗ ████║██╔══██╗██╔══██╗██║ ██╔╝    ██║   ██║██║██║
  ███████║██║  ██║███████║    ██╔████╔██║███████║██████╔╝█████╔╝     ██║   ██║██║██║
  ██╔══██║██║  ██║██╔══██║    ██║╚██╔╝██║██╔══██║██╔══██╗██╔═██╗     ╚██╗ ██╔╝██║██║
  ██║  ██║██████╔╝██║  ██║    ██║ ╚═╝ ██║██║  ██║██║  ██║██║  ██╗     ╚████╔╝ ██║██║
  ╚═╝  ╚═╝╚═════╝ ╚═╝  ╚═╝    ╚═╝     ╚═╝╚═╝  ╚═╝╚═╝  ╚═╝╚═╝  ╚═╝      ╚═══╝  ╚═╝╚═╝
```

**The Next-Generation Desktop-Native Autonomous AI Operating Layer**  
*Cognitive Architecture • Liquid Dynamic Island • Verbal "Hey ADA" Wake Engine • 3D Holographic Neural Interface • Genuine Real-Time Hardware & ADB Telemetry*

---

[![Python 3.11+](https://img.shields.io/badge/Python-3.11%2B-blue.svg?style=for-the-badge&logo=python&logoColor=white)](https://python.org)
[![FastAPI](https://img.shields.io/badge/FastAPI-0.109%2B-009688.svg?style=for-the-badge&logo=fastapi&logoColor=white)](https://fastapi.tiangolo.com)
[![TypeScript](https://img.shields.io/badge/TypeScript-5.0%2B-3178C6.svg?style=for-the-badge&logo=typescript&logoColor=white)](https://www.typescriptlang.org)
[![React 19](https://img.shields.io/badge/React-19.0%2B-61DAFB.svg?style=for-the-badge&logo=react&logoColor=black)](https://react.dev)
[![Electron](https://img.shields.io/badge/Electron-30.0%2B-47848F.svg?style=for-the-badge&logo=electron&logoColor=white)](https://www.electronjs.org)
[![Three.js](https://img.shields.io/badge/Three.js-0.160%2B-black.svg?style=for-the-badge&logo=threedotjs&logoColor=white)](https://threejs.org)
[![License MIT](https://img.shields.io/badge/License-MIT-green.svg?style=for-the-badge)](LICENSE)

[Architecture](#system-architecture) • [Dynamic Island](#liquid-dynamic-island) • [Wake Word Engine](#autonomous-hey-ada-verbal-wake-engine) • [Acoustic Safety Shield](#acoustic-safety--anti-hallucination-shield) • [Live Telemetry](#100-genuine-real-time-telemetry) • [Desktop & Phone Automation](#cross-platform-automation-matrix) • [Quick Start](#installation--setup) • [Documentation Hub](#master-documentation-index)

</div>

---

## Executive Overview

**ADA Mark VII** (Autonomous Digital Assistant) is an intelligent, privacy-first, desktop-native Operating Layer designed to bridge the chasm between human thought and digital execution. 

Unlike traditional chatbots that remain trapped inside browser tabs, ADA integrates directly with your host operating system and mobile environment:
- **Always-Available Dynamic Island**: A floating, screen-saver level liquid capsule centered at the top of your workspace that expands on hotkeys (<kbd>Alt+Space</kbd> / <kbd>F2</kbd>) or verbal cues.
- **Autonomous Verbal Wake-Word Engine**: Ambient background listener that detects **"Hey ADA"** at the OS level, responds orally with **"Yes, Boss?"** in her signature British Sonia HD studio voice, and captures your spoken directive with **Groq Whisper-large-v3-turbo (~150ms)**.
- **Acoustic Safety & Anti-Hallucination Shield**: Hardware RMS energy gating, zero-verb Whisper prompt priming, and silence hallucination filtering that eliminate accidental triggers or spontaneous executions.
- **Genuine Hardware & ADB Telemetry**: Zero mocked or randomized metrics. Live monitoring of 16 host CPU threads, physical RAM consumption, and real-time battery status from connected Android devices over Wi-Fi ADB (`dumpsys battery`).
- **Full Automation Matrix**: Native Windows UI controllers (Notepad, Calculator, File Explorer), Playwright headless/headed browser automations, and wireless Android phone control (screen wake, unlock, gesture dispatch, WhatsApp/Instagram messaging with safety interlocks).
- **3D Holographic Neural Interface**: Interactive Three.js synaptic neural network with customizable HUD matrix, directive execution streams, and orbital particle physics.

---

## System Architecture

ADA follows a decoupled, high-performance client-server topology combining a **Python 3.11 asynchronous FastAPI/Kernel daemon** with an **Electron / React 19 holographic client** communicating over dual full-duplex WebSockets.

```mermaid
flowchart TB
    subgraph Host_Environment ["Host OS & Peripherals"]
        MIC["Microphone Array<br/>(Realtek Audio)"]
        SPEAKER["System Audio Output<br/>(Sonia HD Studio TTS)"]
        HARDWARE["Hardware Sensors<br/>(psutil / 16 Threads / RAM)"]
        ANDROID["Android Smartphone<br/>(Wi-Fi ADB / 192.168.0.x:5555)"]
    end

    subgraph Frontend_Electron ["Frontend Layer (Electron + React 19 + Three.js)"]
        ISLAND["Dynamic Island Window<br/>(Liquid Morphing Capsule)"]
        DASHBOARD["Main Holographic Dashboard<br/>(3D Neural Synapse + HUD)"]
        WS_CLIENT["Dual WebSocket Client<br/>(/ws/chat & /ws/events)"]
        STORE["Zustand Store<br/>(Telemetry, Chat, Widgets)"]
    end

    subgraph Backend_Kernel ["Backend Layer (Python 3.11 + FastAPI + AsyncIO)"]
        API["FastAPI REST & WS Engine<br/>(Port 8000)"]
        WAKE["WakeWordService Daemon<br/>(speech_recognition + RMS Gate)"]
        ROUTER["Capability Router & Planner<br/>(Intent Resolution)"]
        KERNEL["Nova Autonomous Kernel<br/>(Pipeline Execution)"]
        MEMORY["Hybrid Memory Engine<br/>(ChromaDB Vector + SQLite)"]
        DEVICES["DeviceManager (ADB)<br/>(Safety Interlocks)"]
    end

    subgraph External_Cognition ["AI Intelligence Providers"]
        GROQ["Groq Cloud<br/>(Llama 3.3 70B & Whisper Turbo)"]
        GEMINI["Google Gemini API<br/>(Gemini 2.5 Flash / Multimodal)"]
        EDGE_TTS["Microsoft Edge TTS<br/>(en-GB-SoniaNeural Studio Voice)"]
    end

    MIC --> WAKE
    WAKE -->|"WAKE_WORD_DETECTED<br/>'Yes, Boss?'"| API
    WAKE -->|"Groq Whisper<br/>~150ms Transcribe"| GROQ
    API <-->|Full Duplex WS| WS_CLIENT
    WS_CLIENT --> ISLAND
    WS_CLIENT --> DASHBOARD
    DASHBOARD --> STORE
    ISLAND --> STORE
    HARDWARE -->|Real-time Poll| API
    ANDROID <-->|Wireless ADB| DEVICES
    DEVICES <--> API
    KERNEL --> ROUTER
    ROUTER --> MEMORY
    ROUTER --> GROQ
    ROUTER --> GEMINI
    ROUTER --> DEVICES
    API -->|Synthesized MP3/WAV| SPEAKER
    EDGE_TTS --> API
```

---

## Core Capabilities & Features

### 1. Liquid Dynamic Island
The Dynamic Island floats continuously at the top-center of your primary display across all virtual desktops and full-screen applications.

- **Collapsed State**: Sleek 320×42px glassmorphic capsule displaying live operational status (`ADA • Online`), pulsing microphone, reactive audio waveform, and quick shortcut pill (<kbd>Alt+Space / F2</kbd>).
- **Expanded State**: Spring-physics animation (`stiffness: 410, damping: 32`) morphing to 480×182px, revealing quick action chips (Morning Briefing, Desktop Organizer, Phone Bridge, Deep Web Research) and fluid directive input.
- **Multi-State Reactive Feedback**:
  - `voice-listening`: Concentric sonar rings, glowing cyan microphone pulse, and audio level visualization.
  - `thinking`: Rotating neural circuit indicator with dynamic status message (*"Planning execution..."* / *"Synthesizing briefing..."*).
  - `executing`: Real-time execution step stream.
  - `error`: Subtle rose warning indicator with auto-recovery.

```
+-------------------------------------------------------------------------+
|  [●] ADA • Online        ||||| (Audio Wave)          [Alt+Space / F2]   |
+-------------------------------------------------------------------------+
                                 │  (Alt+Space or "Hey ADA")
                                 ▼
+-------------------------------------------------------------------------+
|  [🎤] LISTENING TO YOU, BOSS...                        17:05            |
|  ─────────────────────────────────────────────────────────────────────  |
|  [ ⚡ Morning Briefing ]  [ 📁 Organize Desktop ]  [ 📱 Phone Bridge ]   |
|  ┌───────────────────────────────────────────────────────────────────┐  |
|  │ Type directive or speak your command...                       [↑] │  |
|  └───────────────────────────────────────────────────────────────────┘  |
+-------------------------------------------------------------------------+
```

---

### 2. Autonomous "Hey ADA" Verbal Wake Engine

ADA features a dedicated, low-latency background audio listener that operates system-wide, even when all windows are minimized or full-screen applications are running.

```mermaid
sequenceDiagram
    autonumber
    actor User as User (Voice)
    participant Mic as Microphone Array
    participant Wake as WakeWordService (Daemon)
    participant Sonia as Audio Player (WAV)
    participant Whisper as Groq Whisper Turbo
    participant Kernel as Nova Cognitive Kernel
    participant Island as Dynamic Island

    User->>Mic: "Hey ADA"
    Mic->>Wake: Ambient Audio Buffer (16kHz PCM)
    Wake->>Wake: Check RMS Energy (Threshold > 100)
    Wake->>Whisper: Transcribe with Zero-Verb Priming
    Whisper-->>Wake: Recognized "Hey ADA"
    Wake->>Island: WS: WAKE_WORD_DETECTED ("Yes, Boss?")
    Island->>Island: Morph to 'voice-listening' (Cyan Ring)
    Wake->>Sonia: Play yes_boss_1.wav ("Yes, Boss?")
    Sonia-->>User: Oral Audio: "Yes, Boss?" (0ms Network Latency)
    Note over Wake: Mute Mic for playback buffer to prevent acoustic feedback
    Wake->>Island: WS: WAKE_WORD_LISTENING ("Listening to you, Boss...")
    Wake->>Wake: Open 6.5s Active Follow-Up Capture Window
    User->>Mic: "What is my phone battery?"
    Mic->>Wake: Command Audio Stream
    Wake->>Whisper: Stream WAV to Whisper-large-v3-turbo (~150ms)
    Whisper-->>Wake: "What is my phone battery?"
    Wake->>Kernel: Dispatch Directive
    Kernel-->>Island: WS: "Your phone battery is currently at 88%."
    Kernel-->>User: Sonia HD Oral Voice: "Your phone battery is at 88%."
```

- **Natural Wake Variations**: Phonetically matches `Hey Ada`, `Ada`, `Hi Ada`, `Hello Ada`, `Okay Ada`, `Ay Ada`, and `A.D.A.`
- **Pre-Rendered Studio Voice Chimes**: Uses pre-synthesized neural clips ([`yes_boss_1.wav`](backend/voice/wake_responses/yes_boss_1.wav) through [`yes_boss_5.wav`](backend/voice/wake_responses/yes_boss_5.wav)) with `en-GB-SoniaNeural` for zero-delay verbal acknowledgement.
- **Acoustic Self-Muting**: Automatically silences microphone input during speech synthesis to prevent self-triggering feedback loops.
- **Dual Invocation Modes**:
  1. *Two-Step Conversational*: Say *"Hey ADA"* ➔ She replies *"Yes, Boss?"* ➔ Speak your command.
  2. *Single-Breath Directive*: Say *"Hey ADA, check my battery"* ➔ She acknowledges and executes immediately without waiting for a second sentence.

---

### 3. Acoustic Safety & Anti-Hallucination Shield

To guarantee that ADA **never executes autonomous or spontaneous actions on ambient silence**, three layers of acoustic protection are active 24/7:

1. **Pure-Python RMS Acoustic Energy Gating**:
   Before transmitting any audio to cloud APIs, the listener computes the Root-Mean-Square (RMS) amplitude directly on the raw 16-bit PCM bytes:
   $$\text{RMS} = \sqrt{\frac{1}{N}\sum_{i=1}^N x_i^2}$$
   If $\text{RMS} < 100$, the buffer (silence, room fan hum, typing, far-field murmur) is discarded in $<2\text{ms}$ with zero network calls.

2. **Zero-Verb Whisper Prompt Priming**:
   Whisper uses its `prompt` parameter as preceding conversational context. When quiet audio is transcribed, Whisper hallucinates whatever words appear in `prompt`. ADA enforces strict zero-verb priming:
   ```python
   prompt = "Hey Ada. ADA is an AI assistant."  # Primes assistant name; NO verbs or app names
   ```
   Whisper can never hallucinate application names (Spotify, WhatsApp, Chrome) on faint noise.

3. **Silence Hallucination Blacklist**:
   Recognized tokens matching known Whisper silence artifacts (`"Thank you"`, `"Thanks for watching"`, `"Subtitles by"`, `"Please subscribe"`, `"Bye"`) are dropped before triggering the cognitive router.

4. **Messaging Safety Interlocks**:
   In [`backend/devices/core.py`](backend/devices/core.py), sending WhatsApp, Instagram, or Telegram messages strictly verifies the contact recipient. If `contact` is empty or unspecified, the action is rejected immediately (`"Cannot send message: No recipient contact specified."`), preventing accidental messages to visible chat lists.

---

### 4. 100% Genuine Real-Time Telemetry

ADA rejects mocked and randomized data. Every metric shown across the HUD and Dynamic Island is collected live from the host operating system and connected hardware:

| Telemetry Component | Metric Source | Verified Specifications |
| :--- | :--- | :--- |
| **Synapse Processor** | `psutil.cpu_percent(percpu=True)` | **16 Logical Threads (10 Physical Cores)**, real-time load bars per thread, **2.40 GHz** clock. |
| **System Memory (RAM)** | `psutil.virtual_memory()` | Physical host RAM (**12.2 / 15.7 GB**, live utilization gauge & nominal health status). |
| **Phone Bridge (ADB)** | `adb shell dumpsys battery` | Live Wi-Fi ADB connection (`192.168.0.101:5555`), real battery level (**88% LINKED**), charging state. |
| **Subsystem Matrix** | Internal Kernel Event Bus | Real-time status for Cognitive Core (`ONLINE`), Desktop Controller (`ARMED`), Voice Wake (`ARMED`), and TTS Engine (`SONIA HD`). |
| **Directive Stream** | `useNovaStore.messages` | Live log stream displaying actual user directives, kernel executions, and assistant responses (zero fake tickers). |

---

### 5. 3D Holographic Neural Interface

Rendered using **Three.js** and **React Three Fiber (@react-three/fiber)**:
- **Holographic Synaptic Sphere**: 150+ dynamic neural vertices connected with pulsing cyan synaptic arcs that morph in real-time based on audio amplitude and processing state.
- **Orbital Synaptic Rings**: Triple nested gyroscope rings rotating with slight counter-phase precession.
- **Ambient HoloDust**: 150 particle holographic dust field with upward drift and additive alpha blending.
- **Audio Visualizer Orb**: Centered glowing core reacting directly to microphone amplitude and TTS playback frequency.

---

### 6. Cross-Platform Automation Matrix

```
                        ┌───────────────────────────────┐
                        │      NOVA CAPABILITY ROUTER   │
                        └──────────────┬────────────────┘
                                       │
         ┌─────────────────────────────┼─────────────────────────────┐
         ▼                             ▼                             ▼
┌──────────────────┐          ┌──────────────────┐          ┌──────────────────┐
│   DESKTOP API    │          │  WEB BROWSER     │          │  ANDROID ADB     │
├──────────────────┤          ├──────────────────┤          ├──────────────────┤
│ • Window Manager │          │ • Playwright     │          │ • Wi-Fi Auto-ADB │
│ • File Explorer  │          │ • Chrome Engine  │          │ • Screen Wake    │
│ • Notepad        │          │ • Multi-Tab Exec │          │ • PIN Unlock     │
│ • Calculator     │          │ • Web Extraction │          │ • WhatsApp Auto  │
│ • Win32 Shell    │          │ • Screenshot OCR │          │ • Instagram Auto │
└──────────────────┘          └──────────────────┘          └──────────────────┘
```

- **Native Windows Controllers**:
  - `FileExplorerController`: Navigate paths, list directories, organize desktop/downloads, batch move files.
  - `NotepadController`: Launch notepad, write notes, save documents with automatic path resolution.
  - `CalculatorController`: Trigger calculations, clear registers, read results.
- **Browser Automation (Playwright)**:
  - Headless and headed chromium execution for automated research, multi-source data extraction, and form interaction.
- **Android ADB Wireless Bridge**:
  - Automated zeroconf / mDNS detection of connected Android devices on local subnet.
  - Automated screen wake, PIN unlock swipe, app launcher (`monkey -p com.whatsapp`), contact search, and message dispatch.
  - State-aware self-healing UI Automator navigation (`uiautomator dump`) that checks active screens, clears search overlays, and dismisses soft keyboards automatically.

---

## Global Keyboard Shortcuts

| Shortcut | Scope | Description |
| :--- | :--- | :--- |
| <kbd>Alt</kbd> + <kbd>Space</kbd> | Global (System-wide) | Toggle Dynamic Island (Expand / Collapse) |
| <kbd>F2</kbd> | Global (System-wide) | Quick toggle Dynamic Island capsule |
| <kbd>Alt</kbd> + <kbd>D</kbd> | Global (System-wide) | Toggle 3D Holographic Main Dashboard |
| <kbd>F9</kbd> | Global (System-wide) | Quick toggle Main Dashboard window |
| <kbd>Ctrl</kbd> + <kbd>Shift</kbd> + <kbd>Space</kbd> | Global | Secondary shortcut to open Main Dashboard |
| <kbd>Escape</kbd> | Dynamic Island | Collapse Dynamic Island back to pill |
| <kbd>Enter</kbd> | Chat / Directive | Dispatch command to cognitive kernel |

---

## REST & WebSocket API Reference

The backend daemon listens on `http://127.0.0.1:8000` (and `0.0.0.0:8000` for LAN bridges).

### REST Endpoints

| Method | Endpoint | Description |
| :--- | :--- | :--- |
| `GET` | `/health` | Health check verifying kernel and subsystem status. |
| `GET` | `/api/telemetry` | Real hardware telemetry: 16 CPU threads, RAM GB/%, ADB battery, active AI model. |
| `GET/POST`| `/api/tts` | Studio neural voice synthesis (`en-GB-SoniaNeural`) with MP3 stream output. |
| `POST` | `/api/voice/transcribe` | Ultra-fast audio transcription via Groq Whisper-large-v3-turbo (~150ms). |
| `GET` | `/api/voice/wake/status` | Returns active status of the "Hey ADA" background wake word listener (`running`, `speaking`, `energy_threshold`). |
| `POST` | `/api/voice/wake/toggle` | Programmatically start or stop the background wake word listener. |
| `GET` | `/api/briefing` | Generates oral and written executive briefing with weather and schedule. |
| `GET` | `/api/devices` | Lists connected wireless ADB Android devices and battery levels. |

### WebSocket Channels

- **`/ws/chat`**: Bidirectional real-time conversational channel. Streams partial assistant tokens, user message confirmations, and completion signals.
- **`/ws/events`**: System-wide telemetry event bus. Broadcasts `WAKE_WORD_DETECTED`, `WAKE_WORD_LISTENING`, `KERNEL_STARTED`, `PLANNING_STARTED`, `STREAM_CHUNK`, and `WORKSPACE_RENDER`.

---

## Installation & Setup

### Prerequisites

1. **Python 3.11+** (Ensure Python is added to Windows PATH)
2. **Node.js 18+** & **npm**
3. **Android Platform Tools (ADB)** (Optional, for phone bridge features)
4. **Git**

### 1. Clone Repository

```bash
git clone https://github.com/Codewithjainam7/Nova.git
cd Nova
```

### 2. Configure Environment Variables

Create a `.env` file in the project root:

```env
# AI Provider API Keys
GROQ_API_KEY=gsk_your_groq_api_key_here
GEMINI_API_KEY=AIzaSy_your_gemini_api_key_here

# Voice & Speech Settings
ADA_VOICE=en-GB-SoniaNeural
PRIMARY_PROVIDER=groq
ACTIVE_MODEL=llama-3.3-70b-versatile

# Security
NOVA_ENCRYPTION_KEY=your_secure_32_byte_key_here
```

### 3. Setup Python Backend Environment

```bash
# Navigate to backend and create virtual environment
cd backend
python -m venv .venv

# Activate virtual environment (Windows PowerShell)
.venv\Scripts\Activate.ps1

# Install core dependencies
pip install -r requirements.txt
pip install speechrecognition pyaudio sounddevice edge-tts psutil av
cd ..
```

### 4. Setup Frontend & Build Production Bundle

```bash
cd frontend
npm install
npm run build
cd ..
```

### 5. Launch ADA Mark VII

To start both the FastAPI backend daemon and the Electron client cleanly:

```bash
# Double-click or run from command prompt:
launch_ada.bat
```

*(Alternatively, to run without a command prompt window, execute `launch_ada_silent.vbs`)*.

---

## Troubleshooting & Diagnostics

| Symptom | Probable Cause | Diagnostic Command / Resolution |
| :--- | :--- | :--- |
| **ADA does not wake on "Hey ADA"** | Microphone muted or ambient noise calibrated too high | Check `GET /api/voice/wake/status`. Verify microphone input level in Windows Settings. Speak closer to the microphone. |
| **Spontaneous task execution** | Whisper prompt hallucination (historical bug) | Ensure you are on latest commit [`6219f4d`](https://github.com/Codewithjainam7/Nova/commit/6219f4d) with zero-verb prompt priming and RMS gating active. |
| **Dynamic Island is blank** | React hook ordering or Electron preload error | Re-run `npm run build` in `frontend/`. Check DevTools (<kbd>Ctrl+Shift+I</kbd>). |
| **Phone Bridge shows "UNLINKED"** | Android Wi-Fi ADB port closed or IP changed | Run `adb devices` in terminal. Re-connect phone with `adb connect <IP>:5555`. |
| **Backend port 8000 in use** | Orphaned uvicorn background process | Run `netstat -ano \| findstr :8000` and terminate with `taskkill /F /PID <PID>`. |

---

## Master Documentation Index

For in-depth architectural deep-dives, developer manuals, and API specifications, consult the 35 master documentation chapters located in [`docs/manual/`](docs/manual/):

- **[Chapter 01: Getting Started & Installation Guide](docs/manual/01_GETTING_STARTED.md)**
- **[Chapter 02: System Architecture Overview](docs/manual/02_ARCHITECTURE_OVERVIEW.md)**
- **[Chapter 03: Autonomous Kernel Subsystem](docs/manual/03_AUTONOMOUS_KERNEL.md)**
- **[Chapter 06: Desktop Automation Engine](docs/manual/06_DESKTOP_AUTOMATION_ENGINE.md)**
- **[Chapter 10: Speech Recognition (STT) Subsystem](docs/manual/10_SPEECH_RECOGNITION_STT.md)**
- **[Chapter 11: Text-to-Speech (TTS) Subsystem](docs/manual/11_TEXT_TO_SPEECH_TTS.md)**
- **[Chapter 12: Full-Duplex Voice Pipeline Orchestration](docs/manual/12_VOICE_PIPELINE_ORCHESTRATION.md)**
- **[Chapter 17: Wireless Android ADB Subsystem](docs/manual/17_ANDROID_ADB_INTEGRATION.md)**
- **[Chapter 20: 3D Neural Brain Canvas (Three.js)](docs/manual/20_3D_NEURAL_BRAIN_CANVAS.md)**
- **[Chapter 21: Holographic HUD & Dynamic Island](docs/manual/21_HOLOGRAPHIC_HUD_AND_UI_COMPONENTS.md)**
- **[Chapter 24: REST & WebSocket API Reference](docs/manual/24_REST_API_REFERENCE.md)**
- **[Chapter 26: Troubleshooting & Diagnostic Matrix](docs/manual/26_TROUBLESHOOTING_AND_FAQ.md)**
- **[Chapter 35: Master Navigation Hub](docs/manual/README.md)**

---

## Security & Privacy Constitution

- **Local Execution First**: Hardware telemetry, desktop automation, and memory retention operate entirely on-device.
- **Credential Protection**: All API keys, environment credentials, and device pins are isolated via `.env` and strictly excluded from version control.
- **Explicit Permissions**: External file modifications, messaging actions, and shell commands require explicit user verification or armed mode toggling.

---

## License

Distributed under the **MIT License**. See [`LICENSE`](LICENSE) for complete terms.

<div align="center">
<b>ADA Mark VII</b> • Engineered with precision by <a href="https://github.com/Codewithjainam7">Jainam Jain</a>
</div>
