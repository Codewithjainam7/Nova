# Chapter 23: Security Model & Permission Architecture

## Overview
ADA implements a strict zero-trust security model (`backend/services/credentials.py` and `frontend/src/components/Permissions/PermissionDialog.tsx`).

## Key Security Pillars
1. **Credential Encryption**: API keys and OAuth tokens are encrypted at rest using AES-GCM-256 via `NovaCredentialManager`.
2. **Interactive Permission Dialogs**: Any destructive action (file modification, process termination, system shutdown) pauses pipeline execution until the user explicitly grants permission in the UI.
3. **Log Sanitization**: Application loggers strip tokens, passwords, and sensitive keys from output streams.
4. **Safe Native APIs**: Replaced unsafe shell calls (`os.system`) with type-safe Win32 C-API bindings (`ctypes.windll`).
