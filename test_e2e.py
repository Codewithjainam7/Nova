import asyncio
import websockets
import json
import traceback

COMMANDS = [
    "Open Notepad and write Hello",
    "Open Google",
    "Open Spotify",
    "Take a screenshot",
    "Read the text on my screen",
    "Remember my favorite color is blue",
    "What is my favorite color?",
]

async def test_with_events(cmd: str):
    print(f"\n{'='*60}")
    print(f"TEST: {cmd}")
    print(f"{'='*60}")
    
    events = []
    
    async def listen_events():
        try:
            async with websockets.connect("ws://localhost:8000/ws/events", open_timeout=10) as ws:
                while True:
                    msg = await asyncio.wait_for(ws.recv(), timeout=60)
                    data = json.loads(msg)
                    t = data.get("type", "")
                    c = data.get("content", "")
                    print(f"  [EVENT] {t}: {str(c)[:500]}")
                    events.append(data)
                    if t == "RESPONSE_COMPLETED":
                        break
        except Exception as e:
            print(f"  [EVENT LISTENER ERROR] {e}")
    
    async def send_chat():
        await asyncio.sleep(0.5)
        try:
            async with websockets.connect("ws://localhost:8000/ws/chat", open_timeout=10) as ws:
                await ws.send(json.dumps({"content": cmd, "conversation_id": "trace1"}))
                while True:
                    msg = await asyncio.wait_for(ws.recv(), timeout=60)
                    data = json.loads(msg)
                    msg_type = data.get("type", "")
                    content = data.get("message", {}).get("content", "")
                    if msg_type == "message_complete":
                        print(f"  [FINAL RESPONSE] {content}")
                        break
        except Exception as e:
            print(f"  [CHAT ERROR] {e}")
    
    await asyncio.gather(listen_events(), send_chat())

async def main():
    await asyncio.sleep(1)
    for cmd in COMMANDS:
        await test_with_events(cmd)
        await asyncio.sleep(2)

asyncio.run(main())
