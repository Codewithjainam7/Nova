# Edge TTS Integration

## Overview
NOVA utilizes [edge-tts](https://github.com/rany2/edge-tts) to handle local Text-to-Speech (TTS) synthesis. This package interfaces directly with the Microsoft Edge TTS API, allowing for high-quality, natural-sounding neural voices without requiring an Azure API key.

## Advantages
- **Cost**: Completely free.
- **Quality**: Utilizes state-of-the-art Azure Neural voices.
- **Latency**: Sub-second TTFB (Time To First Byte), making it highly suitable for conversational AI.

## Voice Selection
By default, the Voice Engine is configured to use:
- **Voice ID**: `en-US-JennyNeural`

## Data Pipeline
The Edge TTS service returns an MP3-encoded byte stream. Because the NOVA `AudioPlayer` leverages `sounddevice` (which natively only plays raw PCM arrays), the system decodes the MP3 on the fly:
1. `edge-tts` streams MP3 bytes via `Communicate(text, voice).stream()`.
2. PyAV (`av`) opens the in-memory byte buffer and decodes the audio streams into frames.
3. The frames are converted to transposed NumPy arrays.
4. `sounddevice` plays the concatenated raw arrays.
