from enum import Enum


class GameState(Enum):
    STARTING = "starting"  # Game is about to start
    ACTIVE = "active"  # Game has started
    FINISHED = "finished"  # Game finished


class RoundState(Enum):
    CHOOSING_CARDS = "choosing_cards"  # Players choosing their cards
    LEADER_CHOOSING = "leader_choosing"  # Leader choosing winner
    ROUND_ENDED = "round_ended"  # Round finished


class WebsocketEvents(Enum):
    ROUND_STARTED = "round_started"
    PLAYER_CARDS_UPDATED = "player_cards_updated"
    PLAYER_JOINED = "player_joined"
    ROUND_STATE_CHANGED = "round_state_changed"
    PLAYER_RECONNECTED = "player_reconnected"
    PLAYER_CREATED = "player_created"
    PLAYER_SELECTED_CARD = "player_selected_card"
    PLAYER_PROFILE_UPDATED = "player_profile_updated"
