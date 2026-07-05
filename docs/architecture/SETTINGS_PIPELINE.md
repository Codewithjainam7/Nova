# NOVA Settings Pipeline

This document visualizes how configuration flows from a User UI update down into the central store, and how runtime modules fetch it.

## 1. UI Update Pipeline
```mermaid
sequenceDiagram
    participant User
    participant UI as Settings UI
    participant Sys as SettingsSystem
    participant Perms as SettingsPermissions
    participant Val as SettingsValidator
    participant Store as SettingsStore
    
    User->>UI: Toggle "Enable Strict Sandbox"
    UI->>Sys: update_setting({key: "strict_sandbox", value: true})
    
    Sys->>Perms: can_write()
    Perms-->>Sys: Authorized
    
    Sys->>Val: validate()
    Val-->>Sys: Schema OK
    
    Sys->>Sys: Apply to Memory Profile
    Sys->>Store: save_profile()
    Store-->>Sys: Disk Write Complete
    
    Sys-->>UI: Update Acknowledged
```

## 2. Runtime Retrieval Pipeline
```mermaid
flowchart TD
    A[Core Runtime Boot] --> B[PluginManager]
    A --> C[SearchManager]
    A --> D[EmailManager]
    
    B --> E[SettingsSystem.get_setting]
    C --> E
    D --> E
    
    E --> F{Permissions Check}
    F -- Blocked --> G[Raise PermissionError]
    F -- Allowed --> H[Return Cached Memory Value]
    
    H --> B
    H --> C
    H --> D
```
