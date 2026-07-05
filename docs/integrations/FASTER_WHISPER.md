# Faster Whisper Integration

## Overview
NOVA uses [faster-whisper](https://github.com/SYSTRAN/faster-whisper) as the primary local Speech-to-Text (STT) engine. It is a reimplementation of OpenAI's Whisper model using CTranslate2, offering significantly faster performance and lower memory usage compared to the original transformers implementation.

## Model Selection
By default, the engine initializes the `base` model. This model strikes an optimal balance for local development on Windows:
- **Disk Space**: ~150 MB
- **VRAM/RAM Required**: ~500 MB
- **Speed**: Extremely fast, capable of sub-second inference for short phrases.

## Configuration
The `SpeechRecognizer` in `backend/voice/providers.py` is configured as follows:
```python
self.model = WhisperModel(self.model_size, device="cpu", compute_type="int8")
```
- **Device**: Pinned to CPU by default for maximum compatibility out-of-the-box. (Can be changed to `cuda` if an NVIDIA GPU is present).
- **Compute Type**: `int8` quantization further reduces the memory footprint without a severe degradation in accuracy.

## Data Pipeline
Raw audio is captured via `sounddevice` as int16 bytes.
Before being passed to the `transcribe` function, it is converted into a normalized float32 NumPy array, as expected by the Whisper architecture:
```python
audio_array = np.frombuffer(audio, np.int16).astype(np.float32) / 32768.0
```
