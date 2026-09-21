# Chapter 10: Speech Recognition (STT) Subsystem

## Overview
ADA features high-speed voice transcription via Groq Cloud's `whisper-large-v3-turbo` model, delivering real-time human-level speech recognition in under 150 milliseconds.

## Audio Processing Pipeline
1. **Frontend Capture**: The client captures microphone audio via `MediaRecorder` using `audio/webm;codecs=opus` chunks.
2. **Streaming & VAD**: The audio analysis hook tracks silence intervals (3.5s timeout) to auto-detect utterance completion.
3. **HTTP Audio Ingestion**: The raw WebM audio buffer is streamed to `/api/voice/transcribe`.
4. **Whisper Transcription**: Groq parses the audio with custom domain prompt conditioning (`"Ada, Spotify, Settings, Windows"`).
5. **Fallback Mechanism**: In the event of network interruption, the engine automatically falls back to Gemini Audio transcription.
