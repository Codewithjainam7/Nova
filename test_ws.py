import asyncio
import websockets
import json

async def test_workspace():
    # Connect to both websockets
    try:
        chat_ws = await websockets.connect('ws://127.0.0.1:8000/ws/chat')
        events_ws = await websockets.connect('ws://127.0.0.1:8000/ws/events')
        
        # Send the query
        print("Sending query to chat...")
        await chat_ws.send(json.dumps({"content": "What is the latest news about the Iran war?", "conversation_id": "test1234"}))
        
        # Listen on events for WORKSPACE_RENDER
        print("Listening for WORKSPACE_RENDER event...")
        while True:
            try:
                event_data = await asyncio.wait_for(events_ws.recv(), timeout=15.0)
                event = json.loads(event_data)
                print(f"Received event: {event.get('type')}")
                if event.get('type') == 'WORKSPACE_RENDER':
                    print("SUCCESS: Workspace Render event triggered!")
                    print("Payload:", json.dumps(event.get('payload'), indent=2))
                    break
            except asyncio.TimeoutError:
                print("Timeout waiting for event.")
                break
                
        await chat_ws.close()
        await events_ws.close()
    except Exception as e:
        print(f"Test failed: {e}")

if __name__ == "__main__":
    asyncio.run(test_workspace())
