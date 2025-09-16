from enum import Enum


class GameState(Enum):
    WAITING = "waiting"  # Waiting for players to join
    STARTING = "starting"  # Game is about to start
    IN_PROGRESS = "in_progress"  # Game is active
    ROUND_ACTIVE = "round_active"  # Round is active, players choosing cards
    ROUND_ENDING = "round_ending"  # Leader choosing winner
    FINISHED = "finished"  # Game finished


class RoundState(Enum):
    CHOOSING_CARDS = "choosing_cards"  # Players choosing their cards
    LEADER_CHOOSING = "leader_choosing"  # Leader choosing winner
    ROUND_ENDED = "round_ended"  # Round finished
