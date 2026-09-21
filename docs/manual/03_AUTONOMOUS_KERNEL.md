# Chapter 03: Autonomous Kernel Subsystem

## Overview
The ADA Kernel (`backend/kernel/core.py`) serves as the central coordinating authority of the operating system. It orchestrates the pipeline between user input reception, cognitive deliberation, resource locking, permission escalation, and task dispatch.

## Kernel State Machine
The kernel transitions strictly through predefined deterministic states:
- `BOOTING`: Initial runtime verification and memory initialization.
- `INITIALIZING`: Loading drivers, ADB network listeners, and provider registries.
- `IDLE`: Listening for wake-words, WebSocket connections, or UI triggers.
- `PLANNING`: Cognitive parsing of natural language intent into structured JSON task graphs.
- `EXECUTING`: Concurrent or sequential execution of desktop, browser, or device tasks.
- `VERIFYING`: Post-execution OCR/state confirmation that the requested goal was reached.
- `ERROR_RECOVERY`: Automatic backoff and alternative route invocation upon failure.

## Dependency Injection (DI) Container
To ensure testability and loose coupling, ADA employs a lightweight, thread-safe Dependency Injection container (`backend/core/di.py`):
```python
from backend.core.di import di_container, bootstrap_di

# Bootstrap all system singletons
bootstrap_di()

# Resolve subsystem on demand
planner = di_container.resolve(PlannerCore)
desktop = di_container.resolve(DesktopEngine)
```

## Pipeline Execution Flow
The execution pipeline (`backend/kernel/pipeline.py`) manages the end-to-end lifecycle of a session:
1. Receives raw input query (text or voice transcript).
2. Augments input with short-term and semantic long-term memory context.
3. Requests task plan from `PlannerCore`.
4. Dispatches tasks via `CapabilityRouter`.
5. Synthesizes a clean, natural confirmation response.
