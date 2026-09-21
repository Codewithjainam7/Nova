# Chapter 01: Getting Started with ADA / NOVA OS

## Introduction
ADA (formerly NOVA) is a state-of-the-art autonomous AI Operating System and JARVIS-class desktop assistant designed for real-time human-AI interaction, multi-modal command execution, local desktop automation, browser orchestration, and wireless Android mobile control.

## System Prerequisites
- **Operating System**: Windows 10 / Windows 11 (64-bit)
- **Python**: Python 3.10 to Python 3.14 (Virtual Environment recommended)
- **Node.js**: v18.0.0+ and npm v9+
- **Rust / Cargo** (Optional for Tauri builds): Rust 1.70+
- **Hardware**:
  - Minimum 8 GB RAM (16 GB recommended for local vector store and 3D WebGL HUD)
  - Microphone & Speakers / Headset for full-duplex voice interface
  - Modern GPU with WebGL 2.0 support for 3D Neural Brain visualization

## Quickstart Guide

### 1. Clone the Repository
```bash
git clone https://github.com/Codewithjainam7/Nova.git
cd Nova
```

### 2. Configure Environment Variables
Copy the example environment file and add your API keys:
```bash
cp .env.example .env
```
Key configuration items:
- `GEMINI_API_KEY`: Google Gemini Pro / Flash API key for cognitive planning.
- `GROQ_API_KEY`: Groq Cloud API key for ultra-fast Whisper Speech-to-Text inference.

### 3. Backend Setup
```bash
cd backend
python -m venv .venv
.venv\Scripts\activate
pip install -r requirements.txt
```

### 4. Frontend Setup
```bash
cd ../frontend
npm install
```

### 5. Launching ADA
To start both the Backend Kernel and Frontend UI simultaneously:

**Terminal 1 (Backend):**
```bash
.venv\Scripts\python.exe -m backend.main
```
*The backend API server boots up at `http://localhost:8000` with WebSocket hubs active at `/ws/chat` and `/ws/events`.*

**Terminal 2 (Frontend):**
```bash
npm run dev
```
*Access the holographic WebGL user interface at `http://localhost:5173`.*
