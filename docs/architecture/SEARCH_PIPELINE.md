# NOVA Search Pipeline Validation

This document illustrates the execution flow for translating raw search queries into verified, ranked knowledge for the Context Engine.

## 1. End-to-End Search Execution Sequence
```mermaid
sequenceDiagram
    participant Kernel as NOVA Kernel
    participant SE as Search Engine
    participant Cache as Search Cache
    participant Pipe as Search Pipeline
    participant Reg as Provider Registry
    participant Web as Web Adapter
    participant News as News Adapter
    participant Rank as Ranker
    participant Ver as Verifier
    participant Context as Context Engine

    Kernel->>SE: search("OpenAI latest model", ["WEB", "NEWS"])
    
    SE->>Cache: get("OpenAI latest model")
    Cache-->>SE: Miss (None)
    
    SE->>Pipe: run()
    Pipe->>Reg: get_providers(["WEB", "NEWS"])
    
    par Async Fetch
        Pipe->>Web: search()
        Web-->>Pipe: Results[]
    and
        Pipe->>News: search()
        News-->>Pipe: Results[]
    end
    
    Pipe->>Rank: rank(Combined Results)
    Rank-->>Pipe: Sorted & Deduped Results
    
    Pipe->>Ver: verify(Top 5 Results)
    Ver-->>Pipe: Verified Results
    
    Pipe-->>SE: Verified Results
    SE->>Cache: set(Results)
    
    SE-->>Kernel: Verified Results
    Kernel->>Context: Inject into Context
```

## 2. Failover and Timeout Flow
```mermaid
sequenceDiagram
    participant Pipe as Search Pipeline
    participant Web as Web Adapter (Fails)
    participant Local as Local Adapter (Succeeds)
    
    Pipe->>Web: search()
    Pipe->>Local: search()
    
    Web-->>Pipe: TimeoutError
    Local-->>Pipe: Results[]
    
    Pipe->>Pipe: Log Web Failure, Proceed with Local
    Pipe->>Ranker: rank(Local Results)
```

## 3. Data Flow Diagram
```mermaid
flowchart LR
    A[Query String] --> B[SearchQueryBuilder]
    B --> C[SearchQuery DTO]
    
    C --> D[Provider Adapters]
    D --> E[Raw SearchResults]
    
    E --> F[SearchRanker]
    F -->|Weighted Scoring| G[Ranked Results]
    
    G --> H[SearchVerifier]
    H -->|Verified| I[Final Result List]
```
