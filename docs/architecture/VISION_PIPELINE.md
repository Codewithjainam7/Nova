# NOVA Vision Pipeline Validation

This document illustrates the execution flow for translating raw pixels from the Desktop or Browser engines into semantic bounding boxes used by the Execution Engine.

## 1. End-to-End Vision Execution Sequence
```mermaid
sequenceDiagram
    participant EE as Execution Engine
    participant DE as Desktop Engine
    participant VE as Vision Engine
    participant Pipe as Vision Pipeline
    participant Prep as Preprocessor
    participant OCR
    participant UI as Object Detector

    EE->>DE: Capture Screenshot
    DE-->>EE: image_bytes
    
    EE->>VE: analyze_screen(image_bytes)
    VE->>Pipe: run_pipeline()
    
    Pipe->>Prep: normalize(image_bytes)
    Prep-->>Pipe: clean_bytes
    
    par Vision Analysis
        Pipe->>OCR: extract(clean_bytes)
        OCR-->>Pipe: TextBoxes
    and
        Pipe->>UI: detect(clean_bytes)
        UI-->>Pipe: UIBoundaries
    end
    
    Pipe->>Pipe: Merge Results
    Pipe-->>VE: VisionResult
    
    VE->>VE: update_cache()
    VE-->>EE: VisionResult
    
    EE->>EE: Map LLM target to Coordinates
    EE->>DE: Mouse Click (X, Y)
```

## 2. OCR Recovery Flow
```mermaid
sequenceDiagram
    participant Exec as Vision Executor
    participant Pipe as Vision Pipeline
    participant OCR as Primary OCR (Tesseract)
    participant Fallback as Fallback OCR (Windows)

    Exec->>Pipe: run_pipeline()
    Pipe->>OCR: extract()
    
    OCR-->>Pipe: Crash / Timeout
    Pipe-->>Exec: Exception
    
    Exec->>Exec: RecoveryManager.handle_failure()
    
    Exec->>Pipe: run_pipeline(use_fallback=True)
    Pipe->>Fallback: extract()
    Fallback-->>Pipe: TextBoxes
    Pipe-->>Exec: Success
```

## 3. Data Flow Diagram
```mermaid
flowchart LR
    A[Raw Screenshot] --> B[Image Preprocessor]
    B --> C[Normalized Tensor / Image]
    
    C --> D[Tesseract Engine]
    C --> E[YOLO / UI Model]
    
    D -->|Text + Boxes| F[Merger]
    E -->|Classes + Boxes| F
    
    F --> G[VisionResult DTO]
    G --> H[Execution Engine]
```
