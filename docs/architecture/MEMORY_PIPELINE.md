# NOVA Memory Validation Pipelines

This document maps out the specific execution flows for all fundamental CRUD and maintenance operations within the Memory Engine.

## 1. Store Flow
```mermaid
sequenceDiagram
    participant Caller
    participant Core
    participant Embedder
    participant DB
    participant Cache

    Caller->>Core: add(MemoryItem)
    Core->>Embedder: embed(content)
    Embedder-->>Core: List[float]
    Core->>DB: add(item)
    Core->>Cache: set(item)
    Core-->>Caller: Success
```

## 2. Retrieve Flow
```mermaid
sequenceDiagram
    participant Caller
    participant Core
    participant Embedder
    participant DB
    participant Ranker

    Caller->>Core: search(MemoryQuery)
    Core->>Embedder: embed(query.text)
    Embedder-->>Core: vector
    Core->>DB: vector_search(query, vector)
    DB-->>Core: List[MemoryItem]
    
    loop Every Item
        Core->>DB: Update last_accessed_at
    end
    
    Core->>Ranker: rank(results)
    Ranker-->>Core: sorted_results
    Core-->>Caller: Top K
```

## 3. Update Flow
```mermaid
sequenceDiagram
    participant Caller
    participant Core
    participant DB
    participant Cache

    Caller->>Core: update(MemoryItem)
    Core->>DB: update(item)
    Core->>Cache: set(item)
    Core-->>Caller: Success
```

## 4. Forget Flow (Manual)
```mermaid
sequenceDiagram
    participant Caller
    participant Core
    participant DB
    participant Cache

    Caller->>Core: forget(memory_id)
    Core->>DB: delete(memory_id)
    Core->>Cache: delete(memory_id)
    Core-->>Caller: Success
```

## 5. Background Maintenance Flow (Cleanup)
```mermaid
sequenceDiagram
    participant Scheduler
    participant Engine
    participant Consolidator
    participant Cleaner
    participant DB
    participant Cache

    Scheduler->>Engine: run_maintenance()
    
    Engine->>Consolidator: consolidate()
    Consolidator->>DB: Merge Similar Items
    
    Engine->>Cleaner: clean()
    Cleaner->>DB: get_all()
    
    loop Every Item
        alt expires_at < now
            Cleaner->>DB: delete(item)
            Cleaner->>Cache: delete(item)
        end
    end
```

## 6. Backup Flow (Future/WIP)
```mermaid
sequenceDiagram
    participant Admin
    participant DB_Driver
    participant Filesystem
    
    Admin->>DB_Driver: trigger_snapshot()
    DB_Driver->>Filesystem: Write state.bin
    Filesystem-->>Admin: Backup Completed
```

## 7. Restore Flow (Future/WIP)
```mermaid
sequenceDiagram
    participant Admin
    participant DB_Driver
    participant Filesystem
    
    Admin->>DB_Driver: restore(state.bin)
    DB_Driver->>Filesystem: Read state.bin
    DB_Driver->>DB_Driver: Rebuild indices
    DB_Driver-->>Admin: Restore Completed
```
