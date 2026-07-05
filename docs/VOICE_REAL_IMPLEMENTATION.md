# Voice Engine Real Implementation

The Phase 1 Voice Engine replaces the mocked architecture with actual hardware recording and local ML inference. 

## Data Flow
```mermaid
sequenceDiagram
    participant Mic as AudioRecorder (sounddevice)
    participant Pipe as STT Engine (faster-whisper)
    participant TTS as TTS Engine (edge-tts)
    participant Spkr as AudioPlayer (sounddevice + PyAV)

    Mic->>Pipe: yield int16 PCM bytes
    Pipe->>Pipe: convert to float32 ndarray
    Pipe-->>TTS: yield final transcript string
    TTS->>TTS: communicate.stream()
    TTS-->>Spkr: yield MP3 bytes
    Spkr->>Spkr: decode MP3 to PCM using PyAV
    Spkr-->>User: sounddevice.play()
```

## Supported Actions
1. **AudioRecorder**: Uses `sounddevice.RawInputStream` running a block size of 100ms. It asynchronously yields chunks using Python's `queue` to avoid blocking the event loop.
2. **AudioPlayer**: Converts standard compressed formats (MP3) back into raw NumPy arrays via `av` (PyAV). Runs synchronously in a background thread to prevent GUI lockups.
3. **SpeechRecognizer**: Leverages `faster-whisper` in CPU mode with `int8` quantization.
4. **SpeechSynthesizer**: Streams from `edge-tts`.
