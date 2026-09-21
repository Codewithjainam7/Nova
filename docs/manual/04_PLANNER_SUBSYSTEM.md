# Chapter 04: Hierarchical Planner Subsystem

## Overview
The Planner (`backend/planner/core.py`) translates unstructured, ambiguous human directives into unambiguous, deterministic execution plans.

## Intent Parsing & Prompt Engineering
The planner leverages structured JSON schema outputs from Gemini 2.0 Flash / Pro. It enforces strict validation:
```json
{
  "plan_id": "uuid",
  "intent": {
    "primary_intent": "Media Control",
    "confidence": 0.98,
    "raw_query": "Play sunflower on Spotify"
  },
  "tasks": [
    {
      "task_id": "1",
      "description": "Play 'sunflower' on Spotify",
      "required_tools": ["desktop"],
      "action_metadata": {
        "app": "spotify",
        "intent": "play_media",
        "entity": "sunflower",
        "desktop_action": "APP_INTENT_EXECUTE"
      }
    }
  ]
}
```

## Key Planning Rules
1. **Desktop-First Execution**: Queries requesting app interactions (Spotify, Windows Settings, Calculator, File Explorer) are routed directly to native OS controllers rather than cloud API OAuth.
2. **Deterministic Risk Assessment**: Actions involving destructive filesystem changes (file deletion, process termination) are flagged with `risk: "HIGH"` to trigger UI permission modals.
3. **Fault-Tolerant Retries**: If the model fails to produce a schema-valid plan, the planner retries up to 3 times with exponential backoff and corrective error prompts.
