# from typing import AsyncIterator

# import pytest
# from websockets.asyncio.server import Server, ServerConnection, serve


# @pytest.fixture
# async def websocket_server() -> AsyncIterator[Server]:
#     async def handler(websocket: ServerConnection) -> None:
#         async for message in websocket:
#             decoded_message = (
#                 message.decode("utf-8") if isinstance(message, bytes) else message
#             )
#             await websocket.send(f"your message was: {decoded_message}")

#     server = await serve(handler, "localhost", 8000)
#     yield server
#     server.close()
#     await server.wait_closed()
