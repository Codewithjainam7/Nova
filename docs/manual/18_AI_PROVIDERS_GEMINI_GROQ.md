# Chapter 18: Multi-LLM Provider Manager

## Overview
The AI Provider Manager (`backend/providers/core.py` and `backend/providers/registry.py`) provides an extensible abstraction layer across multiple cloud and local AI model providers.

## Registered Providers
- **Google Gemini**:
  - Models: `gemini-2.0-flash`, `gemini-1.5-pro`, `gemini-1.5-flash`
  - Purpose: High-capacity cognitive reasoning, hierarchical planning, code generation, and vision analysis.
- **Groq Cloud**:
  - Models: `whisper-large-v3-turbo`, `llama-3.3-70b-versatile`
  - Purpose: Ultra-low latency voice transcription and instant conversational streaming.

## Automatic Failover
If the primary provider encounters rate limits (HTTP 429) or network timeouts, the Provider Manager automatically fails over to secondary registered providers seamlessly.
