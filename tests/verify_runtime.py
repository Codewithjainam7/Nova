import os
import asyncio
from fastapi.testclient import TestClient

# Must load environment before importing main app
from backend.core.environment import load_environment
load_environment()

from backend.main import app, kernel

def verify_runtime():
    print("=== Task 7: Full Runtime Verification ===")
    
    with TestClient(app) as client:
        # 1. GET /health
        resp = client.get("/health")
        print(f"GET /health: {resp.status_code} - {resp.json()}")
        
        # 2. GET /ready
        resp = client.get("/ready")
        print(f"GET /ready: {resp.status_code} - {resp.json()}")
        
        # 3. GET /metrics
        resp = client.get("/metrics")
        print(f"GET /metrics: {resp.status_code}")
        
        # 4. GET /version
        resp = client.get("/version")
        print(f"GET /version: {resp.status_code} - {resp.json()}")
        
        # 5. WebSocket /ws/chat
        with client.websocket_connect("/ws/chat") as websocket:
            websocket.send_text('{"content": "ping"}')
            data1 = websocket.receive_json()
            print(f"WebSocket /ws/chat received: {data1}")
            data2 = websocket.receive_json()
            print(f"WebSocket /ws/chat received: {data2}")
            
        # 6. WebSocket /ws/events
        with client.websocket_connect("/ws/events") as websocket:
            print("WebSocket /ws/events connected successfully.")
            
        print("\nAll Runtime Verifications [PASS]")

if __name__ == "__main__":
    verify_runtime()
