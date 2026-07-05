# NOVA UI Event Pipeline

This document illustrates the one-way event flow from the NOVA Kernel out to the Dynamic Island Presentation Layer.

## 1. End-to-End UI Event Flow
```mermaid
sequenceDiagram
    participant Kernel as NOVA Kernel
    participant EE as Execution Engine
    participant Bus as Event Bus
    participant DI as Dynamic Island
    participant State as Island State Manager
    participant Anim as Island Animator
    participant UI as Frontend User

    Kernel->>EE: execute_task()
    
    %% Execution starts
    EE->>Bus: emit("ExecutionStarted")
    Bus->>DI: dispatch_kernel_event(EXECUTING)
    DI->>State: update(EXECUTING)
    DI->>Anim: trigger(PROGRESS, 1000)
    Anim->>UI: Morph to Progress Widget
    
    %% Execution error
    EE->>Bus: emit("ExecutionFailed")
    Bus->>DI: dispatch_kernel_event(ERROR)
    DI->>State: update(ERROR)
    DI->>DI: NotificationManager.show("Error")
    DI->>Anim: trigger(FADE, 300)
    Anim->>UI: Display Error Notification
    
    %% User Dismisses
    UI->>DI: dispatch_user_interaction("DISMISS_ERROR")
    DI->>DI: NotificationManager.clear()
    DI->>Anim: trigger(COLLAPSE)
```

## 2. Notification Data Flow
```mermaid
flowchart LR
    A[Subsystem Error/Info] --> B[Kernel]
    B --> C[Event Bus]
    C --> D[IslandEventSubscriber]
    
    D --> E{Severity}
    E -- Error/Warning --> F[NotificationManager]
    E -- State Change --> G[StateManager]
    
    F --> H[Render Notification Widget]
    G --> I[Render Main Island Body]
```
