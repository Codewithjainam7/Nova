# NOVA Chat UI Pipeline

This document visualizes the journey of a user message from the UI, down to the Kernel, and the streaming response back up to the UI.

## 1. Chat Pipeline Flow
```mermaid
sequenceDiagram
    participant User
    participant UI as Chat UI (Frontend)
    participant Sys as ChatSystem (Presentation Layer)
    participant Kernel as NOVA Kernel
    participant AI as AI Provider

    User->>UI: Type message and hit Enter
    UI->>Sys: add_message(USER, "Hello")
    Sys->>Sys: Store and Render User Message
    
    UI->>Kernel: dispatch_request("Hello")
    Kernel->>AI: query_model("Hello")
    
    AI-->>Kernel: Async Token Stream
    Kernel-->>Sys: stream_response(Generator)
    
    loop Stream Yields
        Sys->>UI: Update Partial Content (HTML)
    end
    
    Sys->>Sys: Compile Final Message (Markdown parsing)
    Sys->>UI: Render Final Formatted Block
```

## 2. Attachment Pipeline
```mermaid
flowchart LR
    A[User Drags File] --> B[Chat UI]
    B --> C[ChatAttachmentManager]
    
    C --> D{Type}
    D -- Image --> E[Base64 / Blob URI]
    D -- PDF --> F[Extract Text Preview]
    
    E --> G[Render Thumbnail in Chat]
    F --> G
    
    G --> H[Kernel extracts data for AI Context]
```
