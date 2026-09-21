# Chapter 26: Troubleshooting & FAQ

## Common Issues & Solutions

### 1. "Microphone error / Voice recognition error"
- **Cause**: Browser microphone permissions denied or audio device busy.
- **Solution**: Allow microphone access in browser settings (`chrome://settings/content/microphone`). Ensure Groq API key is valid in `.env`.

### 2. "Settings opened but didn't navigate to tab"
- **Cause**: Windows UWP suspension delay.
- **Solution**: ADA automatically uses `ms-settings:` deep-linking URIs. Ensure your Windows build supports standard URI handlers.

### 3. "WebSocket connection closed before establishment"
- **Cause**: Backend server is not running on port 8000.
- **Solution**: Start the backend via `.venv\Scripts\python.exe -m backend.main` and confirm port 8000 is open.

### 4. "ADB Device not recognized"
- **Cause**: Android device and PC must be connected to the exact same Wi-Fi subnet.
- **Solution**: Enable "Wireless Debugging" in Android Developer Options.
