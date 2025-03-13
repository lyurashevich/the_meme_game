from typing import AsyncIterator

import pytest
from websockets.asyncio.client import connect
from websockets.asyncio.server import Server, ServerConnection, serve


@pytest.fixture
async def websocket_server() -> AsyncIterator[Server]:
    async def handler(websocket: ServerConnection) -> None:
        async for message in websocket:
            await websocket.send(f"your message was: {message}")

    server = await serve(handler, "localhost", 8000)
    yield server
    server.close()
    await server.wait_closed()


@pytest.mark.asyncio
async def test_websocket_connection(websocket_server: ServerConnection) -> None:
    url = "ws://localhost:8000/ws/1"
    async with connect(url) as ws:
        await ws.send("hello")
        response = await ws.recv()
        assert response == "your message was: hello"
