# Chapter 22: Real-Time WebSocket Communication

## Overview
Communication between the frontend client and backend kernel occurs over dual high-performance WebSocket channels (`frontend/src/contexts/NovaWebSocket.tsx`).

## WebSocket Endpoints
1. **`/ws/chat`**:
   - Handles user message submissions, token-by-token streaming responses, and execution plan updates.
2. **`/ws/events`**:
   - Streams real-time kernel telemetry, audio amplitude values, device connection events, and system logs.

## Reliability Features
- **Automatic Reconnection**: Reconnects with exponential backoff if the backend restarts.
- **Heartbeat & Keepalive**: Periodically sends ping frames to prevent socket timeouts across proxies.
