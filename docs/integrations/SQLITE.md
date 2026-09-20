# SQLite Database Integration

NOVA utilizes a local SQLite database (`nova_memory.db`) to persist all relational state and metadata.

## Schema
The database manages three core tables:
- `conversations`: Primary keys for distinct chat sessions, pinning status, and timestamps.
- `messages`: One-to-many relationship mapping raw user/assistant messages to their parent conversation.
- `memory_metadata`: A companion table for semantic memories, storing timestamps and importance scores for hybrid joins.

## Philosophy
SQLite acts as the absolute Source of Truth for exact contextual retrieval. The React frontend is entirely stateless and does not send history over the WebSocket. Instead, NOVA's runtime queries SQLite to reconstruct the exact context window before passing it to the AI providers.
