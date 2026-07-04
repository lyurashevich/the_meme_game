from unittest.mock import AsyncMock, patch

import pytest
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from starlette.testclient import TestClient

from app.db import TEST_DATABASE_URL, Base, get_db
from app.game.connection_manager import ConnectionManager
from app.game.dataclasses import Game, Player
from app.game.game_manager import GameManager
from app.main import app
from app.models import MemeCard, SituationCard
from app.services.game_service import GameService
from app.services.player_service import PlayerService
from app.services.reconnect_service import ReconnectService
from app.services.room_service import RoomService

# Configure pytest-asyncio
pytest_plugins = ("pytest_asyncio",)


test_engine = create_engine(TEST_DATABASE_URL, echo=True)
test_session_maker = sessionmaker(test_engine, expire_on_commit=False)


@pytest.fixture
def connection_manager():
    return ConnectionManager()


@pytest.fixture
def room_service():
    return RoomService()


@pytest.fixture
def game_manager():
    return GameManager()


@pytest.fixture
def player_service(connection_manager, room_service):
    return PlayerService(connection_manager, room_service)


@pytest.fixture
def game_service(room_service, game_manager, connection_manager):
    return GameService(room_service, game_manager, connection_manager)


@pytest.fixture
def reconnect_service(room_service, player_service):
    return ReconnectService(room_service, player_service)


@pytest.fixture
def client_with_no_db():
    with TestClient(app) as client:
        yield client


@pytest.fixture
def client(db_session):
    def override_get_db():
        yield db_session

    app.dependency_overrides[get_db] = override_get_db
    return TestClient(app)


@pytest.fixture
def db_session():
    Base.metadata.create_all(bind=test_engine)
    with test_engine.begin() as conn:
        for table in reversed(Base.metadata.sorted_tables):
            conn.execute(table.delete())

    with test_session_maker(bind=test_engine) as session:
        yield session


@pytest.fixture
def test_player(player_service):
    player = Player(username="Lisaveta", id="333")
    player_service.players[player.id] = player
    return player


@pytest.fixture
def test_players():
    people = [Player(id=str(i)) for i in range(3)]
    return people


@pytest.fixture
async def test_room(test_player, room_service, player_service, game_manager):
    room = await room_service.create_room(owner=test_player)
    yield room
    room_service.active_rooms.clear()
    player_service.players.clear()
    game_manager.active_games.clear()


@pytest.fixture
async def test_room_with_players(test_player, test_players, room_service, player_service, game_manager):
    room = await room_service.create_room(owner=test_player)
    for player in test_players:
        room.add_player(player)

    yield room
    room_service.active_rooms.clear()
    player_service.players.clear()
    game_manager.active_games.clear()


@pytest.fixture
async def prepared_game(test_room_with_players, mock_meme_cards, mock_situation_cards, game_service):
    """non-started game yet"""
    with patch("app.services.game_service.MemeService.get_meme_cards", return_value=mock_meme_cards), patch(
        "app.services.game_service.SituationService.get_situation_cards", return_value=mock_situation_cards
    ):
        game = await game_service.prepare_game(room_id=test_room_with_players.id)

    yield game


@pytest.fixture
def test_game(test_room):
    game = Game(room=test_room)
    return game


@pytest.fixture
def mock_meme_cards():
    meme_cards = [MemeCard(id={i}, image_url=f"http://memes.org/{i}") for i in range(30)]

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
