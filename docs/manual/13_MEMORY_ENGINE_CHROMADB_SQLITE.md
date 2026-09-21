# Chapter 13: Hybrid Memory Architecture

## Overview
ADA utilizes a two-tier hybrid memory engine (`backend/memory/`) combining relational structured storage with dense vector semantic search.

## Storage Architecture
1. **Relational SQLite Store (`sqlite_store.py`)**:
   - Stores chronological chat message logs, session metadata, system metrics, and credentials.
   - Enforces referential integrity and fast indexed queries.
2. **Vector ChromaDB Store (`chroma_store.py`)**:
   - Stores dense vector embeddings of past user interactions, preferences, code snippets, and knowledge documents.
   - Supports cosine similarity search for top-k contextual retrieval.

## Memory Compaction
Background workers periodically prune stale ephemeral sessions while preserving high-relevance semantic nodes.
