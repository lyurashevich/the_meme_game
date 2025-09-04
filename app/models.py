import uuid
from dataclasses import dataclass, field
from datetime import datetime, timedelta
from enum import Enum
from typing import List, Optional

from db import Base
from sqlalchemy import Boolean, ForeignKey, Integer, String, Table
from sqlalchemy.orm import Mapped, mapped_column, relationship


class GameState(Enum):
    WAITING = "waiting"  # Waiting for players to join
    STARTING = "starting"  # Game is about to start
    IN_PROGRESS = "in_progress"  # Game is active
    ROUND_ACTIVE = "round_active"  # Round is active, players choosing cards
    ROUND_ENDING = "round_ending"  # Leader choosing winner
    FINISHED = "finished"  # Game finished


class MemeCard(Base):
    __tablename__ = "meme_cards"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    image_url: Mapped[str] = mapped_column(String, nullable=False)


class RoundState(Enum):
    CHOOSING_CARDS = "choosing_cards"  # Players choosing their cards
    LEADER_CHOOSING = "leader_choosing"  # Leader choosing winner
    ROUND_ENDED = "round_ended"  # Round finished


class SituationCard(Base):
    __tablename__ = "situation_cards"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    text: Mapped[str] = mapped_column(String, nullable=False)


@dataclass
class MemeCard:
    id: int
    image_url: str
    round_to_return: Optional[int] = (
        None  # Round when this card can be returned to deck
    )


@dataclass
class SituationCard:
    id: int
    text: str
    round_to_return: Optional[int] = (
        None  # Round when this card can be returned to deck
    )


@dataclass
class Player:
    id: int  # WebSocket connection ID
    username: str
    handed_cards: List[MemeCard] = field(default_factory=list)
    is_host: bool = False  # Host is the first leader
    score: int = 0
    is_connected: bool = True
    connection_order: int = 0  # Order of connection for leader rotation
    # selected_card: Optional[MemeCard] = None  # Card selected for current round


@dataclass
class Room:
    id: str = field(default_factory=lambda: str(uuid.uuid4()))
    name: str = f"room{id}"
    max_players: int = 10
    owner: Optional[Player] = None
    invitation_link: str = field(
        default_factory=lambda: f"https://your-domain.com/join/{uuid.uuid4()}"
    )
    is_private: bool = False
    players: List[Player] = field(default_factory=list)
    # created_at: datetime = field(default_factory=datetime.now)


@dataclass
class GameRound:
    round_number: int
    leader: Player
    situation_card: SituationCard
    player_choices: dict[int, MemeCard] = field(
        default_factory=dict
    )  # player_id -> selected_card
    winner: Optional[Player] = None
    state: RoundState = RoundState.CHOOSING_CARDS
    start_time: datetime = field(default_factory=datetime.now)
    end_time: Optional[datetime] = None
    time_limit: int = 60  # seconds


@dataclass
class Game:
    room: Room
    id: str = field(default_factory=lambda: str(uuid.uuid4()))
    state: GameState = GameState.WAITING
    current_round: Optional[GameRound] = None
    round_number: int = 0
    meme_deck: List[MemeCard] = field(default_factory=list)
    situation_deck: List[SituationCard] = field(default_factory=list)
    meme_discard_pile: List[MemeCard] = field(default_factory=list)
    situation_discard_pile: List[SituationCard] = field(default_factory=list)
    leader_index: int = 0  # Index in players list for current leader
    # created_at: datetime = field(default_factory=datetime.now)
    # ended_at: Optional[datetime] = None


@dataclass
class MemeCardsDeck:
    available_cards: List[MemeCard] = field(default_factory=list)
    used_cards: List[MemeCard] = field(default_factory=list)
    discard_pile: List[MemeCard] = field(default_factory=list)


@dataclass
class SituationCardsDeck:
    available_cards: List[SituationCard] = field(default_factory=list)
    used_cards: List[SituationCard] = field(default_factory=list)
    discard_pile: List[SituationCard] = field(default_factory=list)


@dataclass
class GameSettings:
    cards_per_player: int = 6
    round_time_limit: int = 60  # seconds
    meme_card_cooldown: int = 10  # rounds before card can be used again
    situation_card_cooldown: int = 20  # rounds before card can be used again
    max_rounds: Optional[int] = None  # None for unlimited rounds
    score_to_win: Optional[int] = None  # None for unlimited score


@dataclass
class GameManager:
    """Manages all active games in memory"""

    active_games: dict[str, Game] = field(default_factory=dict)  # room_id -> Game
    active_rooms: dict[str, Room] = field(default_factory=dict)  # room_id -> Room
    player_connections: dict[int, str] = field(
        default_factory=dict
    )  # player_id -> room_id
