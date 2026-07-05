# NOVA Plugin Ecosystem

This document visualizes the journey of a third-party plugin integrating into the NOVA AI Runtime, highlighting the strict sandbox enforcement.

## 1. Plugin Load Ecosystem
```mermaid
sequenceDiagram
    participant OS as File System
    participant Loader as PluginLoader
    participant Registry as PluginRegistry
    participant Sandbox as PluginSandbox

    OS->>Loader: Read `manifest.json`
    Loader->>Loader: Validate Schema & Version
    Loader->>Loader: Verify Digital Signature
    
    alt Validation Failed
        Loader->>Registry: update_state(ERROR)
    else Validation Passed
        Loader->>Registry: update_state(LOADED)
        Registry->>Sandbox: Prepare Runtime Environment
    end
```

## 2. Plugin Execution Ecosystem
```mermaid
flowchart TD
    A[Third-Party Plugin Code] --> B[Plugin Sandbox]
    B --> C{Permission Check}
    
    C -- Unregistered Intent --> D[Block & Log]
    C -- Valid Intent --> E[NOVA Kernel Event Bus]
    
    E --> F[Core Runtime]
    
    %% Engine Dispatch
    F --> G[Browser Engine]
    F --> H[Desktop Engine]
    F --> I[Memory Engine]
    
    G --> J[Format Output]
    H --> J
    I --> J
    
    J --> E
    E --> B
    B --> A
```
