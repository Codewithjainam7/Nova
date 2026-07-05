# NOVA Context Engine Architecture

## 1. Overview
The Context Engine is responsible for collecting, normalizing, filtering, deduplicating, ranking, and compressing all runtime context before an AI request is submitted to the AI Provider Manager. No other module is permitted to inject context directly.

## 2. Responsibilities
- **Context Collection:** Dynamically queries registered `ContextProviders` (Memory, FileSystem, Browser, UI State, execution artifacts).
- **Filtering & Deduplication:** Removes exact duplicates or extremely low-relevance items to preserve token space.
- **Ranking:** Weights context items based on relevance, recency, and importance heuristics.
- **Compression:** Greedily drops the lowest-ranked context items if the total `estimated_tokens` exceeds the system limit.
- **Assembly:** Packages the finalized tokens into a structured `ContextPackage`.

## 3. Internal Components
- **ContextEngine (Core):** Orchestrates the pipeline and tracks metrics (total packages, average tokens).
- **ContextCollector:** Maintains a registry of active `ContextProviders` and fans out collection asynchronously.
- **ContextPipeline:** Linear execution flow calling Filter -> Ranker -> Compressor -> Assembler.
- **ContextFilter:** Enforces threshold cuts and removes hashed duplicates.
- **ContextRanker:** Sorts the filtered context based on a weighted formula.
- **ContextCompressor:** Token-budget enforcer. Drops bottom-ranked context until the budget fits.
- **ContextAssembler:** Converts flat context items into a strongly-typed `ContextPackage`.

## 4. Folder Structure
```text
backend/context/
├── schema.py        # ContextType, ContextItem, ContextPackage
├── collector.py     # ContextProvider ABC, ContextCollector
├── filter.py        # ContextFilter
├── ranker.py        # ContextRanker
├── compressor.py    # ContextCompressor
├── assembler.py     # ContextAssembler
├── pipeline.py      # ContextPipeline (glue layer)
├── core.py          # ContextEngine (Orchestrator)
```

## 5. Mermaid Class Diagram
```mermaid
classDiagram
    class ContextEngine {
        +get_context(): ContextPackage
        +register_provider(provider)
    }
    class ContextPipeline {
        +build_context(): ContextPackage
    }
    class ContextCollector {
        +collect_all(): List[ContextItem]
    }
    class ContextFilter {
        +deduplicate(items)
        +filter_by_threshold(items)
    }
    class ContextRanker {
        +rank(items)
    }
    class ContextCompressor {
        +compress(items)
    }
    class ContextAssembler {
        +assemble(items): ContextPackage
    }

    ContextEngine --> ContextPipeline
    ContextPipeline --> ContextCollector
    ContextPipeline --> ContextFilter
    ContextPipeline --> ContextRanker
    ContextPipeline --> ContextCompressor
    ContextPipeline --> ContextAssembler
```

## 6. Mermaid Flow Diagram
```mermaid
flowchart TD
    A[Execution Engine / Prompt Engine] --> B[ContextEngine]
    B --> C[ContextCollector]
    C --> D[Provider 1]
    C --> E[Provider 2]
    C --> F[Provider N]
    D --> G[Flat List of ContextItems]
    E --> G
    F --> G
    G --> H[ContextFilter: Deduplicate & Threshold]
    H --> I[ContextRanker: Weighted Sort]
    I --> J[ContextCompressor: Token Budgeting]
    J --> K[ContextAssembler: Categorization]
    K --> L[ContextPackage]
    L --> M[Return to Caller]
```

## 7. Mermaid Sequence Diagram
```mermaid
sequenceDiagram
    participant Caller
    participant CE as ContextEngine
    participant CP as ContextPipeline
    participant COL as Collector
    participant FIL as Filter
    participant RAN as Ranker
    participant COM as Compressor
    participant ASM as Assembler

    Caller->>CE: get_context()
    CE->>CP: build_context()
    
    CP->>COL: collect_all()
    COL-->>CP: raw_items
    
    CP->>FIL: deduplicate(raw_items)
    CP->>FIL: filter_by_threshold()
    FIL-->>CP: filtered_items
    
    CP->>RAN: rank(filtered_items)
    RAN-->>CP: ranked_items
    
    CP->>COM: compress(ranked_items)
    COM-->>CP: compressed_items
    
    CP->>ASM: assemble(compressed_items)
    ASM-->>CP: ContextPackage
    
    CP-->>CE: ContextPackage
    CE-->>Caller: ContextPackage
```

## 8. Mermaid State Diagram
```mermaid
stateDiagram-v2
    [*] --> Collecting
    Collecting --> Filtering
    Filtering --> Ranking
    Ranking --> Compressing
    Compressing --> Assembling
    Assembling --> [*]
```

## 9. Dependency Graph
- Depends on: Pydantic, Python asyncio.
- Consumed by: Prompt Engine.

## 10. Public API
- `ContextEngine.register_provider(provider: ContextProvider)`
- `ContextEngine.get_context() -> ContextPackage`

## 11. Design Decisions
- **Fail-Safe Collection:** The Collector catches and suppresses exceptions from individual providers. One failing provider (e.g., Browser disconnected) will not crash the entire context build.
- **Greedy Compression:** Currently utilizes a fast greedy algorithm (top-down inclusion until token limit is hit) rather than expensive knapsack optimization.

## 12. Performance Considerations
- Context retrieval is heavily parallelized in the real implementation (via `asyncio.gather` for providers).
- Exact hashing is used for deduplication which operates in $O(N)$ time.

## 13. Context Lifecycle
1. Providers inject flat generic `ContextItem`s.
2. Items are stripped out or sliced based on constraints.
3. Assembler categorizes them (e.g., `browser_context`, `memory_context`) making it significantly easier for the Prompt Engine to render the template block by block.

## 14. Future Improvements
- **Semantic Deduplication:** Upgrade exact-hash deduplication to cosine similarity checking to merge context items that mean the same thing but have slightly different text.
- **Accurate Tokenization:** Swap dummy token estimator `len(str) // 4` with a real `tiktoken` or `sentencepiece` wrapper.
