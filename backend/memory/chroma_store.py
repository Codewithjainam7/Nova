import os
from typing import List, Optional, Dict, Any
from backend.memory.schema import MemoryItem, MemoryType, MemoryQuery
from backend.core.logger import app_logger

try:
    import chromadb
    from chromadb.config import Settings
except ImportError:
    chromadb = None
    app_logger.warning("chromadb not installed. ChromaVectorStore will fail.")

class ChromaVectorStore:
    def __init__(self, persist_directory: str = "nova_chroma_db"):
        if chromadb is None:
            raise RuntimeError("chromadb is not available.")
            
        self.persist_directory = persist_directory
        # Initialize Persistent Client
        self.client = chromadb.PersistentClient(path=self.persist_directory)
        
        # Get or Create Collection
        self.collection = self.client.get_or_create_collection(
            name="nova_semantic_memory",
            metadata={"hnsw:space": "cosine"}
        )

    def _format_metadata(self, item: MemoryItem) -> Dict[str, Any]:
        """ChromaDB metadata values must be strings, ints, or floats."""
        meta = {
            "memory_type": item.memory_type.value,
            "importance": item.importance,
            "created_at": item.created_at.isoformat(),
        }
        # Flatten simple metadata if needed, but for now just stringify to avoid nested dict errors in Chroma
        for k, v in item.metadata.items():
            if isinstance(v, (str, int, float, bool)):
                meta[f"meta_{k}"] = v
            else:
                meta[f"meta_{k}"] = str(v)
        return meta

    async def add(self, item: MemoryItem):
        if not item.embedding:
            app_logger.warning(f"Cannot add memory {item.memory_id} to ChromaDB without an embedding.")
            return
            
        self.collection.add(
            ids=[item.memory_id],
            embeddings=[item.embedding],
            documents=[item.content],
            metadatas=[self._format_metadata(item)]
        )

    async def get(self, memory_id: str) -> Optional[dict]:
        """Gets raw chroma dict. The orchestrator will merge with SQLite data."""
        results = self.collection.get(ids=[memory_id])
        if results and results["ids"]:
            return {
                "id": results["ids"][0],
                "document": results["documents"][0] if results["documents"] else None,
                "metadata": results["metadatas"][0] if results["metadatas"] else None
            }
        return None

    async def update(self, item: MemoryItem):
        if not item.embedding:
            return
            
        self.collection.update(
            ids=[item.memory_id],
            embeddings=[item.embedding],
            documents=[item.content],
            metadatas=[self._format_metadata(item)]
        )

    async def delete(self, memory_id: str):
        self.collection.delete(ids=[memory_id])

    async def search(self, query: MemoryQuery, query_embedding: List[float]) -> List[str]:
        """Returns a list of memory_ids that match the query."""
        where_filter = {}
        if query.memory_types:
            if len(query.memory_types) == 1:
                where_filter = {"memory_type": query.memory_types[0].value}
            else:
                where_filter = {"$or": [{"memory_type": t.value} for t in query.memory_types]}
        
        # Combine with metadata filters if provided
        for k, v in query.metadata_filter.items():
            if isinstance(v, (str, int, float)):
                where_filter[f"meta_{k}"] = v

        kwargs = {
            "query_embeddings": [query_embedding],
            "n_results": query.top_k,
        }
        
        if where_filter:
            if len(where_filter) == 1:
                kwargs["where"] = where_filter
            else:
                # ChromaDB allows $and for multiple conditions, but for simplicity we rely on basic where if possible, 
                # or just use the first filter if complex logic isn't strictly necessary for the prototype.
                kwargs["where"] = where_filter
        
        results = self.collection.query(**kwargs)
        
        matched_ids = []
        if results and results["ids"]:
            # results["ids"] is a list of lists: [['id1', 'id2']]
            for id_list, distance_list in zip(results["ids"], results["distances"]):
                for i, mem_id in enumerate(id_list):
                    distance = distance_list[i]
                    # Convert distance to similarity (cosine space: similarity = 1 - distance if distance is cosine distance, 
                    # but chromadb cosine distance is 1 - cosine_similarity. So similarity = 1 - distance)
                    similarity = 1.0 - distance
                    if similarity >= query.min_similarity:
                        matched_ids.append(mem_id)
                        
        return matched_ids
