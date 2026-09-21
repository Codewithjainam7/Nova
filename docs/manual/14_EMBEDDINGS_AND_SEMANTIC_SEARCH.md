# Chapter 14: Text Embeddings & Semantic Search

## Overview
The Embedder subsystem (`backend/memory/embedder.py`) converts natural language text into high-dimensional vector representations.

## Embedding Providers
- **Gemini Embeddings**: `text-embedding-004` generates 768-dimensional dense vectors.
- **Local Fallback Embedder**: Built-in deterministic hashing and lightweight embedding models for offline environments.

## Query Augmentation
When a user asks a question referring to past events (e.g., *"What did we configure yesterday?"*), the query vector is compared against stored embeddings in ChromaDB to inject relevant context before prompt assembly.
