# NOVA Desktop Automation Pipeline

This document visualizes the exact pipeline traversal required to convert an abstract AI plan into a physical change on the user's desktop.

## 1. End-to-End Execution Sequence
```mermaid
sequenceDiagram
    participant User
    participant Planner
    participant EE as Execution Engine
    participant Agent as App Agent
    participant Cap as Capability Resolver
    participant DE as Desktop Engine
    participant Exec as Desktop Executor
    participant OS as Windows OS

    User->>Planner: "Open Notepad and type Hello"
    Planner->>EE: Action: Launch Notepad
    
    EE->>Agent: Route to App Agent
    Agent->>Cap: resolve(APP_LAUNCH)
    Cap-->>Agent: Desktop Automation Tool
    
    Agent->>DE: perform_action(APP_LAUNCH, "notepad.exe")
    DE->>Exec: execute()
    
    Exec->>Exec: Check Permissions (Granted)
    Exec->>OS: win32api.CreateProcess("notepad.exe")
    OS-->>Exec: Process Handle
    Exec-->>DE: Success
    DE-->>Agent: Success
    
    EE->>Agent: Action: Type "Hello"
    Agent->>DE: perform_action(KEYBOARD_TYPE, "Hello")
    DE->>Exec: execute()
    Exec->>OS: win32api.keybd_event("Hello")
    OS-->>Exec: Success
    Exec-->>DE: Success
    DE-->>EE: Task Complete
    EE-->>User: "Notepad opened and text typed."
```

## 2. Recovery Pipeline
```mermaid
sequenceDiagram
    participant EE as Execution Engine
    participant DE as Desktop Engine
    participant Exec as Desktop Executor
    participant Disp as Dispatcher
    participant OS as Windows OS

    EE->>DE: perform_action(WINDOW_FOCUS, "Chrome")
    DE->>Exec: execute()
    Exec->>Disp: dispatch()
    Disp->>OS: SetForegroundWindow("Chrome")
    OS-->>Disp: ERROR_INVALID_WINDOW_HANDLE
    
    Disp-->>Exec: Exception Raised
    Exec->>Exec: RecoveryManager: handle_failure()
    
    Exec->>Disp: Retry dispatch()
    Disp->>OS: SetForegroundWindow("Chrome")
    
    alt Retry Fails
        OS-->>Disp: ERROR_INVALID_WINDOW_HANDLE
        Disp-->>Exec: Exception
        Exec-->>DE: Raise Exception
        DE-->>EE: DesktopActionFailed
        EE->>EE: Re-plan (e.g., search for process instead)
    end
```

## 3. Data Flow Diagram
```mermaid
flowchart LR
    A[Execution Engine] -->|DesktopAction| B[Desktop Engine]
    B -->|Check| C[Permission Manager]
    C -->|Dispatch| D[Action Dispatcher]
    D --> E[Mouse Controller]
    D --> F[Keyboard Controller]
    D --> G[Window Manager]
    D --> H[Filesystem Manager]
    
    E --> I((Operating System))
    F --> I
    G --> I
    H --> I
    
    I -->|Latency / Status| B
```
