import asyncio

from connection_manager import ConnectionManager
from fastapi import APIRouter
from redis_client import redis_client
from starlette.responses import HTMLResponse
from starlette.websockets import WebSocket, WebSocketDisconnect

router = APIRouter()

manager = ConnectionManager()


@router.get("/")
async def get() -> HTMLResponse:
    return HTMLResponse(html)


@router.get("/health")
def health_check() -> dict[str, str]:
    return {"status": "ok"}


@router.websocket("/ws/{client_id}")
async def websocket_endpoint(websocket: WebSocket, client_id: int) -> None:
    await manager.connect(websocket)

    try:
        pubsub = redis_client.pubsub()
        await pubsub.subscribe(f"channel: {client_id}")

        async def listen_to_redis_messages() -> None:
            try:
                while True:
                    msg = await pubsub.get_message(ignore_subscribe_messages=True)
                    if msg:
                        await manager.broadcast(msg["data"].decode())
            except Exception as e:
                print(f"error in listen_to_redis_messages: {e}")

        asyncio.create_task(listen_to_redis_messages())

        while True:
            data = await websocket.receive_text()
            print(f"received message from client {client_id}: {data}")
            await manager.send_personal_message(f"your message was: {data}", websocket)
            await redis_client.publish(
                f"channel: {client_id}", f"client #{client_id} says {data}"
            )

    except WebSocketDisconnect:
        await manager.disconnect(websocket)
        print(f"client #{client_id} disconnected")
        await redis_client.publish(
            f"channel {client_id}", f"client #{client_id} left the chat"
        )
        await redis_client.close()


html = """
<!DOCTYPE html>
<html>
    <head>
        <title>Chat</title>
    </head>
    <body>
        <h1>WebSocket Chat</h1>
        <form action="" onsubmit="sendMessage(event)">
            <input type="text" id="messageText" autocomplete="off"/>
            <button>Send</button>
        </form>
        <ul id='messages'>
        </ul>
        <script>
            var client_id = Math.floor(Math.random() * 1000);
            var ws = new WebSocket(`ws://localhost:8000/ws/${client_id}`);
            ws.onmessage = function(event) {
                var messages = document.getElementById('messages')
                var message = document.createElement('li')
                var content = document.createTextNode(event.data)
                message.appendChild(content)
                messages.appendChild(message)
            };
            function sendMessage(event) {
                var input = document.getElementById("messageText")
                ws.send(input.value)
                input.value = ''
                event.preventDefault()
            }
        </script>
    </body>
</html>
"""
