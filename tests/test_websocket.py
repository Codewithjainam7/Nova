import asyncio
import websockets
import json

async def test_websocket():
    uri = "ws://localhost:8000/ws/chat"
    try:
        async with websockets.connect(uri) as websocket:
            print("Connected to WebSocket!")
            
            payload = json.dumps({"content": "Hello", "conversation_id": "test_conv_1"})
            print(f"Sending: {payload}")
            await websocket.send(payload)
            
            # Wait for streaming responses
            while True:
                response = await websocket.recv()
                data = json.loads(response)
                print(f"Received: {data}")
                
                if data.get("type") == "message_complete":
                    print("Stream completed.")
                    break
                    
    except Exception as e:
        print(f"WebSocket test failed: {e}")

if __name__ == "__main__":
    asyncio.run(test_websocket())
