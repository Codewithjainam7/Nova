# Chapter 15: Context Engine & Token Optimization

## Overview
The Context Engine (`backend/context/core.py`) gathers, ranks, filters, and compresses disparate system states into a token-optimized context package.

## Context Aggregation Pipeline
1. **Collector Phase**: Gathers current OS state, active window titles, clipboard contents, recent chat history, and semantic memory matches.
2. **Ranking & Prioritization**: Scores each context chunk by recency, relevance, and task priority.
3. **Compression & Truncation (`compressor.py`)**: Drops low-priority items when the estimated token count approaches the configured ceiling (`max_tokens=4000`).
4. **Assembly**: Packs the final sanitized context into a `ContextPackage` for the AI model.
