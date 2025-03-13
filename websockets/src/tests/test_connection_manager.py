from unittest.mock import AsyncMock

import pytest

from ..connection_manager import ConnectionManager


@pytest.mark.asyncio
async def test_connect() -> None:
    manager = ConnectionManager()
    mock_websocket = AsyncMock()

    await manager.connect(mock_websocket)
    assert len(manager.active_connections) == 1
    assert mock_websocket in manager.active_connections


@pytest.mark.asyncio
async def test_disconnect() -> None:
    manager = ConnectionManager()
    mock_websocket = AsyncMock()

    await manager.connect(mock_websocket)

    await manager.disconnect(mock_websocket)
    assert len(manager.active_connections) == 0
    assert mock_websocket not in manager.active_connections


@pytest.mark.asyncio
async def test_send_personal_message() -> None:
    manager = ConnectionManager()
    mock_websocket = AsyncMock()

    await manager.connect(mock_websocket)

    await manager.send_personal_message("hello", mock_websocket)
    mock_websocket.send_text.assert_called_once_with("hello")


@pytest.mark.asyncio
async def test_broadcast() -> None:
    manager = ConnectionManager()
    mock_websocket1 = AsyncMock()
    mock_websocket2 = AsyncMock()

    await manager.connect(mock_websocket1)
    await manager.connect(mock_websocket2)

    await manager.broadcast("hello everyone")
    mock_websocket1.send_text.assert_called_once_with("hello everyone")
    mock_websocket2.send_text.assert_called_once_with("hello everyone")
