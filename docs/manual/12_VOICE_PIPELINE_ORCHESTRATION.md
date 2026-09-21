# Chapter 12: Full-Duplex Voice Pipeline Orchestration

## Overview
The Voice Pipeline orchestrates the continuous, low-latency conversational loop between human speech and autonomous execution.

## Voice Loop Sequence Diagram
```
User Speaks ---> [MediaRecorder] ---> [Groq Whisper STT]
                                              |
                                     (Transcribed Query)
                                              |
                                              v
                                      [Planner Core]
                                              |
                                      (Executable Plan)
                                              |
                                              v
                                    [Capability Router]
                                       /              \
                           [Desktop Action]       [Browser Action]
                                       \              /
                                              v
                                     [Kernel Response]
                                              |
                                              v
                                     [Frontend TTS Voice] ---> Speaker Output
```

## Latency Breakdown
- **STT Transcription**: ~150 ms
- **Plan Generation**: ~800 ms
- **Action Execution**: ~200 ms
- **TTS Synthesis**: Instantaneous (Web Speech API)
- **Total Turnaround**: ~1.15 seconds
