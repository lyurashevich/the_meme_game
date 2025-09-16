from dataclasses import dataclass
from typing import Optional


@dataclass
class GameSettings:
    cards_per_player: int = 6
    round_time_limit: int = 60  # seconds
    meme_card_cooldown: int = 10  # rounds before card can be used again
    situation_card_cooldown: int = 20  # rounds before card can be used again
    max_rounds: Optional[int] = None  # None for unlimited rounds
    score_to_win: Optional[int] = None  # None for unlimited score
