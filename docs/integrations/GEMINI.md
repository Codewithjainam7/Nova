# Google Gemini Integration

NOVA natively integrates with the `google-genai` SDK to power its primary LLM capabilities.

## Supported Models
- `gemini-2.5-flash` (Default)
- `gemini-2.5-pro` (Optional upgrade for complex reasoning)

## Setup
To use Gemini, you must set the following environment variables in `.env` or `.env.local`:
```env
GEMINI_API_KEY=your_api_key_here
GEMINI_DEFAULT_MODEL=gemini-2.5-flash
```

## Architecture
- **Unary:** `GeminiProvider.generate` wraps `client.aio.models.generate_content`.
- **Streaming:** `GeminiProvider.generate_stream` wraps `client.aio.models.generate_content_stream` and translates it into NOVA `StreamingToken` chunks.
- **Failover:** If Gemini fails or times out, the `ProviderManager` automatically falls back to Groq.
