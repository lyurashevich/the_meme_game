import random
import uuid
from dataclasses import dataclass, field
from datetime import datetime

from faker.proxy import Faker

from app.exceptions import PlayerNotInRoomException
from app.game.enums import GameState, RoundState
from app.game.game_settings import GameSettings
from app.models import MemeCard, SituationCard
from app.schemas.round import PlayerChoiceSchema

AVATARS = ("cat", "frog", "capybara", "doge", "hamster", "pigeon")


@dataclass
class ReconnectToken:
    player_id: str
    expires_at: datetime | None


@dataclass
class Player:
    username: str = ""
    avatar_id: str | None = None
    id: str = field(default_factory=lambda: str(uuid.uuid4())[:8])
    hand_cards: list[MemeCard] = field(default_factory=list)
    is_host: bool = False  # Host is the first leader
    score: int = 0
    is_connected: bool = True
    connection_order: int = 0  # Order of connection for leader rotation
    room_id: str | None = None

    def __post_init__(self):
        if not self.username:
            self.username = Faker().name()

        if not self.avatar_id:
            self.avatar_id = random.choice(AVATARS)  # nosec B311 - game logic only, not cryptography


@dataclass
class Room:
    settings: GameSettings = field(default_factory=GameSettings)

    name: str | None = None
    id: str = field(default_factory=lambda: str(uuid.uuid4()))
    max_players: int = 10
    owner: Player | None = None
    # invitation_link: str = field(default_factory=lambda: f"https://your-domain.com/join/{uuid.uuid4()}")
    invitation_link: str | None = None
    is_private: bool = False
    players: list[Player] = field(default_factory=list)
    messages: list[dict] = field(default_factory=list)
    # created_at: datetime = field(default_factory=datetime.now)

    @property
    def owner_id(self) -> str:
        if self.owner is None:
            raise Exception("Owner not found")
        return self.owner.id

    @property
    def owner_name(self) -> str:
        if self.owner is None:
            raise Exception("owner not found")
        return self.owner.username

    @property
    def rounds_count(self) -> int | None:
        return self.settings.round_time_limit

    @property
    def time_limit(self) -> int:
        return self.settings.round_time_limit

    @property
    def players_count(self) -> int:
        return len(self.players)

    def __post_init__(self) -> None:
        if self.name is None:
            self.name = Faker().city()

        if self.owner and self.owner not in self.players:
            self.players.append(self.owner)
            self.players[0].is_host = True

    def add_player(self, player: Player) -> None:
        if len(self.players) >= self.max_players:
            raise Exception("The room is full")
        if player in self.players:
            raise Exception("You have already joined the room!")

        self.players.append(player)

    def remove_player(self, player: Player) -> None:
        if player not in self.players:
            raise PlayerNotInRoomException()

        self.players.remove(player)

    def reassign_owner(self) -> None:
        """Promote the next player in join order to owner.

        Callers are expected to have already removed the departing owner
        from ``self.players``, so ``self.players[0]`` is the longest-standing
        remaining player. Sets ``owner = None`` if no players are left.
        """
        if self.owner is not None:
            self.owner.is_host = False

        if not self.players:
            self.owner = None
            return

        new_owner = self.players[0]
        new_owner.is_host = True
        self.owner = new_owner


@dataclass
class GameRound:
    game: "Game"
    round_number: int
    leader: Player
    situation_card: SituationCard
    player_choices: dict[str, MemeCard] = field(default_factory=dict)  # player_id -> selected_card
    winner: Player | None = None
    state: RoundState = RoundState.CHOOSING_CARDS
    time_limit: int = 60  # seconds
    finalized: bool = False

    @property
    def player_choices_list(self):
        return [
            PlayerChoiceSchema(player_id=player.id, username=player.username, image_url=card.image_url)
            for player_id, card in self.player_choices.items()
            for player in [next(player for player in self.game.room.players if player.id == player_id)]
        ]

    @property
    def situation_card_id(self):
        return self.situation_card.id

    @property
    def game_id(self):
        return self.game.id

    @property
    def leader_id(self):
        return self.leader.id

    @property
    def situation_card_text(self):
        return self.situation_card.text


@dataclass
class Game:
    room: Room
    settings: GameSettings

    current_round: GameRound | None = None
    state: GameState = GameState.STARTING
    id: str = field(default_factory=lambda: str(uuid.uuid4()))
    # round_number: int = 0
    meme_deck: list[MemeCard] = field(default_factory=list)
    situation_deck: list[SituationCard] = field(default_factory=list)
    meme_discard_pile: dict[int, list[MemeCard]] = field(default_factory=dict)
    situation_discard_pile: dict[int, list[SituationCard]] = field(default_factory=dict)
    leader_index: int = 0  # Index in players list for current leader
    # created_at: datetime = field(default_factory=datetime.now)
    # ended_at: Optional[datetime] = None

    @property
    def room_id(self):
        return self.room.id

    @property
    def meme_deck_count(self):
        return len(self.meme_deck)

    @property
    def situation_deck_count(self):
        return len(self.situation_deck)

    @property
    def players(self):
        return [player.id for player in self.room.players]


@dataclass
class MemeCardChoice:
    player: Player
    card: MemeCard

    @property
    def username(self):
        return self.player.username

    @property
    def player_id(self):
        return self.player.id

    @property
    def image_url(self):
        return self.card.image_url
