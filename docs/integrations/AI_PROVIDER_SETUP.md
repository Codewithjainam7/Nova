# AI Provider Setup Guide

To switch NOVA from Mock mode to Production mode, you must configure your API keys for the desired backend providers.

## 1. Environment File

Create or update `.env.local` at the root of the `backend/` directory:

```env
# Primary Provider
GEMINI_API_KEY=your_gemini_key_here

# Fallback Provider
GROQ_API_KEY=your_groq_key_here
```

## 2. Models
By default, the `.env` file uses:
- `GEMINI_DEFAULT_MODEL=gemini-2.5-flash`
- `GROQ_DEFAULT_MODEL=llama-3.3-70b-versatile`

These can be overridden in `.env.local`.

## 3. Streaming and Fallback
The `ProviderManager` automatically detects the keys on boot. If a request to Gemini times out or receives a rate limit, the manager will seamlessly re-route the conversation history to Groq. 

Because both providers now support Native Streaming, the `StreamingToken` data structure maps their chunk formats into a unified schema for the WebSocket layer.
