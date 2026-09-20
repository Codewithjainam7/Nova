# Groq Integration

NOVA natively integrates with the `groq` SDK to serve as the ultra-fast secondary/fallback LLM provider.

## Supported Models
- `llama-3.3-70b-versatile` (Default Fallback)
- `llama-3.1-8b-instant` (Secondary Fallback)

## Setup
To use Groq, set the following environment variables in `.env` or `.env.local`:
```env
GROQ_API_KEY=your_api_key_here
GROQ_DEFAULT_MODEL=llama-3.3-70b-versatile
```

## Architecture
- **Unary:** `GroqProvider.generate` uses `client.chat.completions.create` (stream=False).
- **Streaming:** `GroqProvider.generate_stream` streams `delta.content` directly to the `StreamingManager`.
- **Failover:** Positioned as the default fallback in `ProviderManager` if the primary (Gemini) encounters a timeout or API error.
