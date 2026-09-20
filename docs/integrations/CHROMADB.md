# ChromaDB Vector Integration

NOVA utilizes a local, persistent ChromaDB instance (`nova_chroma_db`) to store and retrieve high-dimensional semantic memory.

## Embeddings
All semantic embeddings are generated locally via `sentence-transformers` using the `all-MiniLM-L6-v2` model. This guarantees 100% privacy and zero latency overhead from cloud embedding providers.

## Architecture
- **Vector Store**: `ChromaVectorStore` acts as a direct wrapper over `chromadb.PersistentClient`.
- **Hybrid Merging**: ChromaDB only stores the dense vector and stringified metadata for fast similarity distance calculations. When a match is found, the system pivots back to SQLite using the returned UUID to fetch the fully-hydrated object.
- **Maintenance**: Background consolidators run on idle to deduplicate overlapping embeddings and prune low-importance memories.
