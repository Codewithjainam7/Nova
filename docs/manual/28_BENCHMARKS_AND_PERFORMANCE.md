# Chapter 28: Performance Benchmarks & Latency Profiles

## System Latency Profile

| Component | Target Latency | Measured Average | Method |
| :--- | :--- | :--- | :--- |
| **Voice STT** | < 200 ms | **148 ms** | Groq `whisper-large-v3-turbo` |
| **Intent Planner** | < 1000 ms | **780 ms** | Gemini 2.0 Flash |
| **Desktop URI Dispatch** | < 100 ms | **45 ms** | Win32 `os.startfile` |
| **UIA Window Focus** | < 250 ms | **120 ms** | Windows UIAutomation |
| **ChromaDB Vector Recall** | < 50 ms | **18 ms** | Cosine Index Query |
| **WebSocket Event Broadcast**| < 10 ms | **2 ms** | FastAPI Async WebSocket |

## Memory Footprint
- **Backend Runtime**: ~180 MB RAM (idle)
- **Frontend WebGL Canvas**: ~95 MB RAM (60 FPS locked)
