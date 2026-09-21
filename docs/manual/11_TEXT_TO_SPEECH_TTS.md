# Chapter 11: Text-to-Speech (TTS) Subsystem

## Overview
ADA's voice synthesis engine provides clear, natural, and expressive female voice feedback.

## Voice Selection Architecture
- **Strict Female Voice Policy**: The voice selector actively filters browser and system voices for premium female speech models (e.g., `Microsoft Zira`, `Google US English Female`, `Samantha`, `Victoria`).
- **Async Voice Loading**: Handles asynchronous browser voice synthesis initialization with exponential retry checks.
- **Configurable Speech Rates**: Calibrated pitch (1.05) and rate (1.02) for crisp, authoritative, JARVIS-style delivery.
- **Interruption Support**: Speech output is immediately halted when new user voice activity is detected.
