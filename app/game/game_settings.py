from dataclasses import dataclass
from typing import Optional


@dataclass
class GameSettings:
    round_time_limit: int = 60  # seconds
    max_rounds: Optional[int] = None  # None for unlimited rounds
    score_to_win: Optional[int] = None  # None for unlimited score
