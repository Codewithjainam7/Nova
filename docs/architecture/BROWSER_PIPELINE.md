# NOVA Browser Pipeline Validation

This document illustrates the execution flow for translating abstract AI intentions into complex DOM manipulations via the Browser Engine.

## 1. End-to-End Execution Sequence
```mermaid
sequenceDiagram
    participant User
    participant Planner
    participant EE as Execution Engine
    participant Cap as Capability Resolver
    participant BE as Browser Engine
    participant Exec as Browser Executor
    participant PW as Playwright API
    participant Browser
    participant Ver as Verification

    User->>Planner: "Find the latest news on techcrunch"
    Planner->>EE: Action: Navigate to TechCrunch
    
    EE->>Cap: resolve(NAVIGATE)
    Cap-->>EE: Browser Engine
    
    EE->>BE: perform_action(NAVIGATE, "https://techcrunch.com")
    BE->>Exec: execute()
    
    Exec->>PW: page.goto("https://techcrunch.com")
    PW->>Browser: Load URL
    Browser-->>PW: Network Idle
    PW-->>Exec: Success
    Exec-->>BE: Success
    BE-->>EE: Action Complete
    
    EE->>BE: perform_action(EXTRACT_TEXT, ".post-title")
    BE->>Exec: execute()
    Exec->>PW: page.locator(".post-title").all_text_contents()
    PW->>Browser: Query DOM
    Browser-->>PW: List[str]
    PW-->>Exec: List[str]
    Exec-->>BE: List[str]
    
    BE->>Ver: Verify Extraction Success
    Ver-->>BE: Passed
    BE-->>EE: Data Array
    EE-->>User: "Here is the latest news..."
```

## 2. Browser Recovery Flow
```mermaid
sequenceDiagram
    participant EE as Execution Engine
    participant BE as Browser Engine
    participant Exec as Executor
    participant PW as Playwright
    participant Browser

    EE->>BE: perform_action(CLICK, "#hidden-button")
    BE->>Exec: execute()
    
    Exec->>PW: page.click("#hidden-button")
    PW->>Browser: Evaluate DOM
    Browser-->>PW: ElementNotInteractableException
    PW-->>Exec: Exception
    
    Exec->>Exec: RecoveryManager.handle_failure()
    
    Exec->>PW: page.wait_for_selector("#hidden-button", state="visible")
    PW->>Browser: Polling DOM
    
    alt Element Becomes Visible
        Browser-->>PW: Visible
        PW->>Browser: Execute Click
        Browser-->>PW: Success
        PW-->>Exec: Success
        Exec-->>BE: Success
    else Timeout Reached
        PW-->>Exec: TimeoutError
        Exec-->>BE: Raise Exception
        BE-->>EE: ActionFailed
    end
```

## 3. Data Flow Diagram
```mermaid
flowchart LR
    A[Execution Engine] -->|BrowserAction| B[Browser Engine]
    B -->|Permission| C[Permission Manager]
    C -->|Dispatch| D[Action Dispatcher]
    D --> E[DOM Manager]
    D --> F[Navigation Manager]
    D --> G[Download Manager]
    
    E --> H((Playwright Adapter))
    F --> H
    G --> H
    
    H -->|Browser State| B
```
