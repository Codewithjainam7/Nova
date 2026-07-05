# NOVA Security & Penetration Validation

## 1. Overview
The `SecurityValidator` exists to intentionally attempt to break the isolated sandboxes built during the `PluginSystem`, `EmailAgent`, and `ExecutionEngine` implementations.

## 2. Threat Models Validated
1. **Plugin Isolation Bypass:** We inject a mock plugin that attempts to read `C:\Windows\System32` or access the `MemoryEngine` SQLite file directly, asserting that a `PermissionError` is thrown by the `PluginEventBridge`.
2. **Settings Secret Leakage:** We assert that requesting an item with `is_secret=True` without the `ADMIN` role throws a hard access exception.
3. **Prompt Injection (Execution):** We simulate a malicious user prompt attempting to execute arbitrary `bash` commands outside of the approved `ExecutionEngine` tool schema.
4. **Email Sandbox:** We attempt to `SEND` an email using the `READ_ONLY` permission tier to ensure the Agent aborts the provider call natively.

## 3. Compliance
By maintaining strict boundary injection and Role-Based Access Controls (RBAC), NOVA ensures that third-party logic and raw LLM hallucination cannot damage the host OS.
