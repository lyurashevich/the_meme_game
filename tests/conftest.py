from unittest.mock import AsyncMock, patch

import pytest
from httpx2 import ASGITransport, AsyncClient
from sqlalchemy import NullPool
from sqlalchemy.ext.asyncio import async_sessionmaker, create_async_engine
from starlette.testclient import TestClient

from app.config import Settings, get_settings
from app.db import TEST_DATABASE_URL, Base, get_db, get_session_factory
from app.dependencies import (
    build_services,
    get_connection_manager,
    get_game_manager,
    get_game_service,
    get_player_service,
    get_reconnect_service,
    get_room_service,
    get_services,
)
from app.game.dataclasses import Game, Player
from app.main import app
from app.models import MemeCard, SituationCard
from tests.helpers import TEST_ADMIN_TOKEN

# Configure pytest-asyncio
pytest_plugins = ("pytest_asyncio",)


test_engine = create_async_engine(TEST_DATABASE_URL, echo=True, poolclass=NullPool)
test_session_maker = async_sessionmaker(test_engine, expire_on_commit=False)


@pytest.fixture
def override_game_service(game_service):
    app.dependency_overrides[get_game_service] = lambda: game_service
    yield
    app.dependency_overrides.pop(get_game_service, None)


@pytest.fixture(autouse=True)
def services():
    """Fresh services and storage for every test, also injected into the app's dependencies."""
    services = build_services()
    overrides = {
        get_connection_manager: lambda: services.connection_manager,
        get_game_manager: lambda: services.game_manager,
        get_room_service: lambda: services.room_service,
        get_player_service: lambda: services.player_service,
        get_game_service: lambda: services.game_service,
        get_reconnect_service: lambda: services.reconnect_service,
        get_services: lambda: services,
        get_session_factory: lambda: test_session_maker,
    }
    app.dependency_overrides.update(overrides)
    yield services
    for dependency in overrides:
        app.dependency_overrides.pop(dependency, None)
    # disconnects schedule a removal a minute later; don't leave those sleeping past the test
    for task in services.reconnect_service._removal_tasks.values():
        task.cancel()


@pytest.fixture
def admin_headers():
    """Enables the card editing API with a test token; returns the headers that authorize a request."""
    app.dependency_overrides[get_settings] = lambda: Settings(admin_token=TEST_ADMIN_TOKEN)
    yield {"X-Admin-Token": TEST_ADMIN_TOKEN}
    app.dependency_overrides.pop(get_settings, None)


@pytest.fixture
def session_factory():
    return test_session_maker


@pytest.fixture
def connection_manager(services):
    return services.connection_manager


@pytest.fixture
def outbox(connection_manager):
    """Records every message the server sends to clients, as ``(player_id, message)`` in send order."""
    sent = []

    async def record(player_id, message):
        sent.append((player_id, message))

    connection_manager.send_personal_json = record
    return sent


@pytest.fixture
def room_service(services):
    return services.room_service


@pytest.fixture
def game_manager(services):
    return services.game_manager


@pytest.fixture
def player_service(services):
    return services.player_service


@pytest.fixture
def notifier(services):
    return services.notifier


@pytest.fixture
def game_service(services):
    return services.game_service


@pytest.fixture
def reconnect_service(services):
    return services.reconnect_service


@pytest.fixture
def client_with_no_db():
    with TestClient(app) as client:
        yield client


@pytest.fixture
async def client(db_session):
    async def override_get_db():
        yield db_session

    app.dependency_overrides[get_db] = override_get_db

    async with AsyncClient(transport=ASGITransport(app=app), base_url="http://test", follow_redirects=True) as client:
        yield client

    app.dependency_overrides.pop(get_db, None)


@pytest.fixture
async def db_session():
    async with test_engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)

    async with test_engine.begin() as conn:
        for table in reversed(Base.metadata.sorted_tables):
            await conn.execute(table.delete())

    async with test_session_maker() as session:
        yield session


@pytest.fixture
async def test_player(player_service):
    player = Player(username="Lisaveta", id="333")
    await player_service.players.add(player)
    return player


@pytest.fixture
def test_players():
    people = [Player(id=str(i), username=f"user_{i}") for i in range(3)]
    return people


@pytest.fixture
async def test_room(test_player, room_service):
    return await room_service.create_room(owner=test_player)


@pytest.fixture
async def test_room_with_players(test_player, test_players, room_service, player_service):
    room = await room_service.create_room(owner=test_player)
    for player in test_players:
        await player_service.players.add(player)
        room.add_player(player)
        player.room_id = room.id

    return room


@pytest.fixture
async def prepared_game(test_room_with_players, mock_meme_cards, mock_situation_cards, game_service, db_session):
    """non-started game yet"""
    with patch("app.services.game_service.MemeService.get_meme_cards", return_value=mock_meme_cards), patch(
        "app.services.game_service.SituationService.get_situation_cards", return_value=mock_situation_cards
    ):
        game = await game_service.prepare_game(room_id=test_room_with_players.id, db=db_session)

    yield game


@pytest.fixture
def test_game(test_room):
    game = Game(room=test_room, settings=test_room.settings)
    return game


@pytest.fixture
def mock_meme_cards():
    meme_cards = [MemeCard(id=i, image_url=f"http://memes.org/{i}") for i in range(30)]

    from app.services.memes_services import CardService

    CardService.MEME_CARDS = meme_cards
    return meme_cards


@pytest.fixture
def mock_situation_cards():
    situation_cards = [SituationCard(id=int(f"{i}"), text=f"situation {i}") for i in range(5)]

    from app.services.situations_services import CardService

    CardService.SITUATION_CARDS = situation_cards
    return situation_cards


@pytest.fixture
def websocket():
    ws = AsyncMock()
    ws.send_json = AsyncMock()
    ws.send_text = AsyncMock()
    ws.accept = AsyncMock()
    ws.close = AsyncMock()
    return ws
