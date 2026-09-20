# Memory Setup Guide

NOVA utilizes a hybrid DB architecture. The systems will automatically initialize locally when you boot the application, requiring zero external database connections or cloud accounts.

## Local Files
Upon first run, NOVA will generate the following artifacts in your root directory:
1. `nova_memory.db` (SQLite file containing your chat history and metadata).
2. `nova_chroma_db/` (Folder containing your high-dimensional semantic memory indices).

## Embeddings
NOVA downloads the `all-MiniLM-L6-v2` model from HuggingFace upon first initialization of the `MemoryEmbedder`. Depending on your connection, the first query may take an additional 10-20 seconds while the weights are cached locally.

## Portability
Because there is no cloud dependency, migrating your entire AI state is as simple as copying the `.db` file and the `chroma_db` folder to a new machine.
