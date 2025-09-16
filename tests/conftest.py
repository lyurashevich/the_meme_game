import pytest
from sqlalchemy import create_engine, text
from sqlalchemy.orm import sessionmaker
from starlette.testclient import TestClient

from app.db import TEST_DATABASE_URL, Base, get_db
from app.game.dataclasses import Game, Player, Room
from app.main import app
from app.models import MemeCard, SituationCard

# Configure pytest-asyncio
pytest_plugins = ("pytest_asyncio",)


test_engine = create_engine(TEST_DATABASE_URL, echo=True)
test_session_maker = sessionmaker(test_engine, expire_on_commit=False)


@pytest.fixture
def client(db_session):
    def override_get_db():
        yield db_session

    app.dependency_overrides[get_db] = override_get_db
    return TestClient(app)


@pytest.fixture
def db_session():
    with test_engine.begin() as conn:
        for table in reversed(Base.metadata.sorted_tables):
            conn.execute(text(f"TRUNCATE TABLE {table.name} RESTART IDENTITY CASCADE"))

    with test_session_maker(bind=test_engine) as session:
        yield session


@pytest.fixture
def player():
    player = Player(username="Lisaveta", id=1)
    return player


@pytest.fixture
def people():
    people = [Player(id=i) for i in range(3)]
    return people


@pytest.fixture
def room(player):
    room = Room(owner=player)
    return room


@pytest.fixture
def game(room):
    game = Game(room=room)
    return game


@pytest.fixture
def mock_meme_cards():
    meme_cards = [MemeCard(image_url=f"http://memes.org/{i}") for i in range(30)]

    from app.services.memes_services import CardService

    CardService.MEME_CARDS = meme_cards
    return meme_cards


@pytest.fixture
def mock_situation_cards():
    situation_cards = [SituationCard(text=f"situation {i}") for i in range(5)]

    from app.services.situations_services import CardService

    CardService.SITUATION_CARDS = situation_cards
    return situation_cards
