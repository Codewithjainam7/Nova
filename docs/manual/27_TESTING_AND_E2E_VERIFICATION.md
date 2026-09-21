# Chapter 27: Testing Strategy & E2E Verification

## Test Architecture
ADA incorporates unit tests, integration tests, and end-to-end (E2E) hardware automation verification scripts.

## Running Tests

### 1. Test Planner Intent Generation
```bash
python test_planner.py
```
*Validates that natural language queries map to expected tools and action metadata.*

### 2. Test Real-time WebSocket Protocol
```bash
python test_ws.py
```
*Validates `/ws/chat` and `/ws/events` handshake, ping-pong, and streaming.*

### 3. Run Full E2E Verification Suite
```bash
python run_real_tests.py
```
*Runs comprehensive end-to-end integration tests across Desktop, Browser, Memory, and AI providers.*
