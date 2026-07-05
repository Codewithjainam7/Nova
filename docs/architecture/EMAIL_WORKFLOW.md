# NOVA Email Workflow Validation

This document illustrates the specific execution paths for common email operations, ensuring permissions and AI logic are applied correctly.

## 1. AI Drafting Workflow
```mermaid
sequenceDiagram
    participant Kernel as NOVA Kernel
    participant EA as Email Agent
    participant Exec as Executor
    participant Perm as Permission Manager
    participant WF as Workflow
    participant PE as Prompt Engine
    participant LLM as AI Provider

    Kernel->>EA: perform_action(COMPOSE_AI, intent="Decline meeting politely")
    EA->>Exec: execute()
    
    Exec->>Perm: check_permission(COMPOSE_AI)
    Perm-->>Exec: Allowed (COMPOSE or SEND level)
    
    Exec->>WF: process_ai_draft(intent)
    
    WF->>PE: format_prompt("Email Drafter", intent)
    PE-->>WF: Formatted Prompt String
    
    WF->>LLM: request(Formatted Prompt)
    LLM-->>WF: Generated Draft Text
    
    WF-->>Exec: Draft Result DTO
    Exec-->>EA: Success
    EA-->>Kernel: Present Draft to User
```

## 2. Secure Send Workflow
```mermaid
sequenceDiagram
    participant Kernel as NOVA Kernel
    participant EA as Email Agent
    participant Exec as Executor
    participant Perm as Permission Manager
    participant Policy as Policy Engine
    participant Prov as Provider Adapter (Gmail)
    participant Memory as Memory Engine

    Kernel->>EA: perform_action(SEND, payload={recipients: ["bad@malicious.com"]})
    EA->>Exec: execute()
    
    Exec->>Perm: check_permission(SEND)
    Perm-->>Exec: Allowed (SEND level)
    
    Exec->>Policy: evaluate_recipients(["bad@malicious.com"])
    Policy-->>Exec: Violation (Domain Blacklisted)
    
    Exec-->>EA: Raise PermissionError
    EA-->>Kernel: Action Blocked
```

## 3. Read and Summarize Workflow
```mermaid
sequenceDiagram
    participant Kernel as NOVA Kernel
    participant EA as Email Agent
    participant WF as Workflow
    participant Prov as Provider Adapter
    participant PE as Prompt Engine

    Kernel->>EA: perform_action(SUMMARIZE_THREAD, thread_id)
    EA->>WF: summarize_thread()
    
    WF->>Prov: fetch_thread(thread_id)
    Prov-->>WF: List[EmailMessage]
    
    WF->>PE: format_prompt("Summarize", List[EmailMessage])
    PE-->>WF: Formatted Prompt
    
    WF->>WF: Call LLM (abstracted)
    WF-->>EA: Summary Text
    EA-->>Kernel: Summary Text
```
