# Chapter 10: Speech Recognition (STT) Subsystem

## 1. Architectural Overview

ADA's Speech-to-Text (STT) subsystem is engineered to provide continuous, high-fidelity transcription with ultra-low latency (<150ms). Running natively on the host machine as an asynchronous background worker (`WakeWordService`), the subsystem interfaces directly with the host default microphone, acoustic energy analyzers, and cloud-accelerated inference engines.

```
                      +------------------------------------------+
                      |         Default OS Microphone            |
                      |       (Realtek Audio Array 16kHz)        |
                      +--------------------+---------------------+
                                           |
                                           v
                      +--------------------+---------------------+
                      |       speech_recognition Listener        |
                      |   (Dynamic Noise Baseline Calibration)   |
                      +--------------------+---------------------+
                                           | Raw PCM Bytes (16-bit)
                                           v
                      +--------------------+---------------------+
                      |      Pure-Python RMS Energy Gate         |
                      |     RMS < 100 -> Ambient Drop (<1ms)     |
                      +--------------------+---------------------+
                                           | Passes Speech Floor
                                           v
                      +--------------------+---------------------+
                      |      Groq Whisper-large-v3-turbo         |
                      | (Zero-Verb Vocabulary Prompt Priming)    |
                      +--------------------+---------------------+
                                           | Raw Transcription
                                           v
                      +--------------------+---------------------+
                      |   Phantom Hallucination Filter & VAD     |
                      |     (Discards Repetitive Noise Tokens)   |
                      +--------------------+---------------------+
                                           | Verified Transcript
                                           v
                      +--------------------+---------------------+
                      |          WAKE_REGEX Matcher              |
                      |     ("Hey ADA" / "ADA" Detection)        |
                      +------------------------------------------+
```

---

## 2. Audio Capture & Acoustic Energy Gating (RMS)

### 2.1 The Challenge of Acoustic Hallucinations
Generative speech models (such as OpenAI Whisper) utilize autoregressive token decoders. When fed silent or low-volume audio buffers containing ambient noise (computer fan hum, typing, room acoustics, or breathing), unconstrained decoders tend to hallucinate repetitive words or latch onto previous context prompts.

### 2.2 Pure-Python Root-Mean-Square (RMS) Calculation
To prevent silent audio from ever reaching cloud transcription APIs, ADA computes the Root-Mean-Square (RMS) acoustic amplitude directly on the raw 16-bit PCM buffer before dispatching any network request:

$$\text{RMS} = \sqrt{\frac{1}{N} \sum_{i=1}^N x_i^2}$$

Implemented in pure Python using `struct.unpack`, this operation evaluates 80,000 samples (5 seconds of 16kHz 16-bit audio) in under **3 milliseconds** with zero third-party C-extensions or external dependencies:

```python
def calculate_rms(raw_pcm: bytes) -> float:
    """Calculates root-mean-square audio energy of 16-bit PCM buffer in <2ms."""
    if not raw_pcm:
        return 0.0
    count = len(raw_pcm) // 2
    if count == 0:
        return 0.0
    shorts = struct.unpack(f"<{count}h", raw_pcm[:count * 2])
    sum_sq = sum(s * s for s in shorts)
    return math.sqrt(sum_sq / count)
```

### 2.3 Acoustic Thresholding Calibration
- **Dead Silence / Far-Field Hum**: `RMS < 80` -> Immediately dropped.
- **Ambient Room & Keystrokes**: `80 <= RMS < 100` -> Filtered out by the gate.
- **Normal Conversational Speech**: `120 <= RMS < 2500` -> Cleared for Groq Whisper transcription.
- **Baseline Calibration**: On initialization, `SpeechRecognition` samples the room acoustics for 0.8 seconds to dynamically adjust `energy_threshold`, enforced to a safe baseline minimum of `200.0`.

---

## 3. High-Speed Transcription: Groq Whisper Turbo

### 3.1 Inference Engine Specification
- **Model**: `whisper-large-v3-turbo`
- **Provider**: Groq Cloud High-Speed LPU Inference
- **Latency**: ~140ms to 180ms total round-trip time
- **Sample Rate**: 16,000 Hz, 16-bit Mono Linear PCM (WAV)
- **Language**: English (`en`)

### 3.2 Prompt Priming Safety Rules
Whisper accepts an optional `prompt` parameter intended for vocabulary spelling hints. 

> [!CAUTION]
> **Never include action verbs, application names, or commands in Whisper prompt parameters.**
> If `prompt="Hey Ada, Spotify, WhatsApp, Chrome"` is used, Whisper will hallucinate `"Spotify, WhatsApp, Chrome"` whenever audio is faint or quiet.

ADA enforces **Zero-Verb Vocabulary Priming**:
```python
res = client.audio.transcriptions.create(
    file=("audio.wav", wav_bytes),
    model="whisper-large-v3-turbo",
    response_format="json",
    language="en",
    prompt="Hey Ada. ADA is an AI assistant."  # Primes the name "Ada" without action verbs
)
```
This primes Whisper to recognize phonetic variations of "ADA" instead of misinterpreting the wake phrase as "Here", "Heard", or "Ayda", while guaranteeing that no phantom commands can be suggested to the model.

---

## 4. Phantom Hallucination Blacklist Filter

Even with RMS gating, low-volume audio may occasionally produce canonical Whisper hallucination artifacts. ADA applies an explicit post-transcription filter:

```python
HALLUCINATION_BLACK_LIST = {
    "thank you", "thank you.", "thank you very much.", "thanks for watching",
    "thanks for watching!", "subtitles by", "subtitle by", "please subscribe",
    "please subscribe.", "bye.", "you", "mbc", "amara.org", "...",
    "here you go", "here you go."
}
```

If the transcription matches any entry in the blacklist, or has fewer than 3 characters, it is discarded immediately without waking the UI or passing to the planner.

---

## 5. Phonetic Regex Matching (`WAKE_REGEX`)

ADA utilizes a broad phonetic regular expression capable of capturing diverse accents, pronunciation speeds, and colloquialisms:

```python
WAKE_REGEX = re.compile(
    r'\b(?:hey|hi|hello|ok|okay|ay)?\s*(?:ada|ayda|aida|eda|ida|adda|ahda|aada|a\.d\.a\.)\b[\s,.:;!?]*',
    re.IGNORECASE
)
```

Matches include:
- `"Hey Ada"` / `"Hey ADA"`
- `"Ada"` / `"ADA"`
- `"Hello Ada, what's my phone battery"`
- `"Okay Ada"` / `"Ay Ada"`
- `"A.D.A."`

---

## 6. Redundant Fallbacks

In the event of Groq API rate limits, network disconnection, or transient socket timeouts:
1. **Primary**: Groq `whisper-large-v3-turbo` (~150ms).
2. **Secondary Fallback (Local)**: Google Free Speech Recognition (`self.recognizer.recognize_google(audio_data)`).
3. **Tertiary Web Fallback**: Gemini 2.5 Flash Multimodal Audio Understanding via `/api/voice/transcribe`.
