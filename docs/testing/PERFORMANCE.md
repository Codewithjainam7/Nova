# NOVA Performance & Benchmarks

## 1. Overview
The `PerformanceBenchmark` suite enforces strict latency SLA budgets. If any sub-system degrades beyond these thresholds, the pipeline halts and rejects the commit.

## 2. Global Latency Budgets
| Subsystem | Target Latency | Max Permitted |
| :--- | :--- | :--- |
| Settings Load | `< 10ms` | `100ms` |
| Context Retrieval | `< 50ms` | `200ms` |
| Plugin Discovery | `< 100ms` | `1000ms` |
| Search (Aggregated) | `< 250ms` | `800ms` |
| Voice Wake Word | `< 50ms` | `150ms` |
| Token Streaming | `60fps` | `30fps` |

## 3. Stress Testing (`StressTester`)
We flood the `NOVA Kernel` with concurrent simulated requests to validate `asyncio` thread contention and Event Bus message droppage.
- **Goal:** 1,000 concurrent non-blocking requests successfully serialized into the `MemoryEngine`.

## 4. Memory Leak Detection (`MemoryLeakDetector`)
Long-running AI agents are notoriously prone to memory bloat due to growing conversation contexts.
- **Validation:** We simulate a 24-hour uptime with continuous context swapping.
- **Assertion:** Baseline RAM delta `< 50MB` variance.
