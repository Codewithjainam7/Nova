import os
from pathlib import Path
from typing import List, Optional, Dict, Any
from backend.memory.schema import MemoryItem, MemoryType, MemoryQuery
from backend.core.logger import app_logger

try:
    import chromadb
    from chromadb.config import Settings
except ImportError:
    chromadb = None
    app_logger.warning("chromadb not installed. ChromaVectorStore will use in-memory fallback.")

class ChromaVectorStore:
    def __init__(self, persist_directory: str = "nova_chroma_db"):
        if not os.path.isabs(persist_directory):
            root_dir = Path(__file__).resolve().parent.parent.parent
            self.persist_directory = str(root_dir / persist_directory)
        else:
            self.persist_directory = persist_directory
        os.makedirs(self.persist_directory, exist_ok=True)
        self._fallback_store: Dict[str, MemoryItem] = {}
        
        if chromadb is None:
            self.client = None
            self.collection = None
            return
            
        try:
            self.client = chromadb.PersistentClient(path=self.persist_directory)
            self.collection = self.client.get_or_create_collection(
                name="nova_semantic_memory",
                metadata={"hnsw:space": "cosine"}
            )
        except Exception as e:
            app_logger.warning(f"Failed to initialize ChromaDB PersistentClient: {e}. Falling back to in-memory.")
            self.client = None
            self.collection = None

    def _format_metadata(self, item: MemoryItem) -> Dict[str, Any]:
        """ChromaDB metadata values must be strings, ints, or floats."""
        meta = {
            "memory_type": item.memory_type.value,
            "importance": item.importance,
            "created_at": item.created_at.isoformat(),
        }
        for k, v in item.metadata.items():
            if isinstance(v, (str, int, float, bool)):
                meta[f"meta_{k}"] = v
            else:
                meta[f"meta_{k}"] = str(v)
        return meta

    async def add(self, item: MemoryItem):
        if not self.collection:
            self._fallback_store[item.memory_id] = item
            return
            
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
        if not self.collection:
            item = self._fallback_store.get(memory_id)
            if item:
                return {"id": item.memory_id, "document": item.content, "metadata": self._format_metadata(item)}
            return None
            
        results = self.collection.get(ids=[memory_id])
        if results and results["ids"]:
            return {
                "id": results["ids"][0],
                "document": results["documents"][0] if results["documents"] else None,
                "metadata": results["metadatas"][0] if results["metadatas"] else None
            }
        return None

    async def update(self, item: MemoryItem):
        if not self.collection:
            self._fallback_store[item.memory_id] = item
            return
            
        if not item.embedding:
            return
            
        self.collection.update(
            ids=[item.memory_id],
            embeddings=[item.embedding],
            documents=[item.content],
            metadatas=[self._format_metadata(item)]
        )

    async def delete(self, memory_id: str):
        if not self.collection:
            self._fallback_store.pop(memory_id, None)
            return
        self.collection.delete(ids=[memory_id])

    async def search(self, query: MemoryQuery, query_embedding: List[float]) -> List[str]:
        if not self.collection:
            return list(self._fallback_store.keys())[:query.top_k]
            
        where_filter = {}
        if query.memory_types:
            if len(query.memory_types) == 1:
                where_filter = {"memory_type": query.memory_types[0].value}
            else:
                where_filter = {"$or": [{"memory_type": t.value} for t in query.memory_types]}
        
        for k, v in query.metadata_filter.items():
            if isinstance(v, (str, int, float)):
                where_filter[f"meta_{k}"] = v

        kwargs = {
            "query_embeddings": [query_embedding],
            "n_results": query.top_k,
        }
        
        if where_filter:
            kwargs["where"] = where_filter
        
        results = self.collection.query(**kwargs)
        
        matched_ids = []
        if results and results["ids"]:
            for id_list, distance_list in zip(results["ids"], results["distances"]):
                for i, mem_id in enumerate(id_list):
                    distance = distance_list[i]
                    similarity = 1.0 - distance
                    if similarity >= query.min_similarity:
                        matched_ids.append(mem_id)
                        
        return matched_ids
