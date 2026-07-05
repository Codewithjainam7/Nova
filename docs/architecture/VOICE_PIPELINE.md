# NOVA Voice Pipeline Validation

This document illustrates the end-to-end traversal of audio data through the NOVA architecture, from raw hardware capture to LLM response synthesis.

## 1. End-to-End Voice Interaction Sequence
```mermaid
sequenceDiagram
    participant Mic
    participant VAD as VAD / Noise
    participant STT as Recognizer
    participant Eng as VoiceEngine
    participant Kernel
    participant LLM as Provider
    participant RG as ResponseGen
    participant TTS as Synthesizer
    participant Spkr

    Mic->>VAD: raw_audio_stream
    VAD->>STT: clean_audio_stream
    STT-->>Eng: yield "Hey NOVA"
    Eng->>Eng: wake_word_detector.detect() == True
    Eng-->>STT: Trigger Finalize
    STT-->>Eng: "Hey NOVA, what time is it?"
    
    Eng->>Kernel: dispatch(Request)
    Kernel->>LLM: generate()
    LLM-->>Kernel: "It is 4:30 PM."
    
    Kernel->>RG: process("It is 4:30 PM.")
    RG-->>Kernel: ResponseOutput
    
    Kernel->>Eng: speak(ResponseOutput.content)
    Eng->>TTS: synthesize("It is 4:30 PM.")
    TTS-->>Eng: audio_bytes
    Eng->>Spkr: play(audio_bytes)
```

## 2. Audio Processing Pipeline
```mermaid
flowchart LR
    A[Microphone (PCM)] --> B[AudioBuffer]
    B --> C[Echo Canceller]
    C --> D[Noise Suppressor]
    D --> E{VAD Detect?}
    E -- No --> B
    E -- Yes --> F[Speech Recognizer]
```

## 3. Interruption State Machine (Barge-In)
```mermaid
stateDiagram-v2
    [*] --> LISTENING
    LISTENING --> PROCESSING : Wake Word Triggered
    PROCESSING --> SPEAKING : TTS Started
    
    state SPEAKING {
        [*] --> PlayingAudio
        PlayingAudio --> AudioFinished
        PlayingAudio --> Interrupted : New Wake Word Detected
    }
    
    AudioFinished --> IDLE
    Interrupted --> PROCESSING
    IDLE --> [*]
```
