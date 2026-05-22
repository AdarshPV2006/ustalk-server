import asyncio
import json
import os
import websockets
from datetime import datetime

connected_users = {}
message_history = []
MAX_HISTORY = 100


async def handle(ws):
    username = None
    try:
        async for raw in ws:
            data = json.loads(raw)
            msg_type = data.get("type")

            if msg_type == "join":
                username = data.get("username", "Anonymous")
                connected_users[username] = ws
                print(f"[+] {username} joined ({len(connected_users)} online)")

                if message_history:
                    await ws.send(json.dumps({"type": "history", "messages": message_history}))

                await broadcast({"type": "system", "text": f"{username} joined the chat", "username": "System"})

            elif msg_type == "message":
                sender = data.get("sender", username or "Unknown")
                text = data.get("text", "")
                ts = datetime.now().strftime("%H:%M")
                print(f"[<] {sender}: {text}")
                msg = {"type": "message", "username": sender, "text": text, "timestamp": ts}
                message_history.append(msg)
                if len(message_history) > MAX_HISTORY:
                    message_history.pop(0)
                await broadcast(msg)

    except websockets.exceptions.ConnectionClosed:
        pass
    finally:
        if username and username in connected_users:
            del connected_users[username]
            print(f"[-] {username} left ({len(connected_users)} online)")
            await broadcast({"type": "system", "text": f"{username} left the chat", "username": "System"})


async def broadcast(msg):
    msg_str = json.dumps(msg)
    dead = []
    for name, ws in connected_users.items():
        try:
            await ws.send(msg_str)
        except:
            dead.append(name)
    for name in dead:
        connected_users.pop(name, None)


async def main():
    port = int(os.environ.get("PORT", 8080))
    print(" UsTalk WebSocket Server")
    print(f" Listening on ws://0.0.0.0:{port}")
    print(f" Share: ws://<your-ip>:{port}  or  wss://<your-domain>")
    print()
    async with websockets.serve(handle, "0.0.0.0", port):
        await asyncio.Future()

if __name__ == "__main__":
    asyncio.run(main())
