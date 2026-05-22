import secrets
import uuid
from dataclasses import dataclass, field
from datetime import datetime

from app.game.enums import GameState, RoundState
from app.models import MemeCard, SituationCard
from app.schemas.round import PlayerChoiceSchema


@dataclass
class Player:
    id: str = field(default_factory=lambda: str(uuid.uuid4())[:8])
    reconnect_token: str = field(default_factory=lambda: secrets.token_hex(16))
    disconnected_at: datetime | None = None
    username: str | None = None
    handed_cards: list[MemeCard] = field(default_factory=list)
    is_host: bool = False  # Host is the first leader
    score: int = 0
    is_connected: bool = True
    connection_order: int = 0  # Order of connection for leader rotation
    room_id: str | None = None

    def __post_init__(self):
        if not self.username:
            self.username = f"user{self.id}"


@dataclass
class Room:
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
    def players_count(self) -> int:
        return len(self.players)

    def __post_init__(self) -> None:
        if self.name is None:
            self.name = f"room{self.id[:8]}"

        if self.owner and self.owner not in self.players:
            self.players.append(self.owner)
            self.players[0].is_host = True

    async def add_player(self, player: Player) -> None:
        if len(self.players) >= self.max_players:
            raise Exception("The room is full")
        if player in self.players:
            raise Exception("You have already joined the room!")

        self.players.append(player)

    async def remove_player(self, player: Player) -> None:
        if player not in self.players:
            raise Exception("User not found")

        self.players.remove(player)


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
