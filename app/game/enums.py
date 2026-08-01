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
    PLAYER_CREATED = "player_created"
    PLAYER_RECONNECTED = "player_reconnected"
    PLAYER_DISCONNECTED = "player_disconnected"
    PLAYER_PROFILE_UPDATED = "player_profile_updated"

    ROOM_CREATED = "room_created"
    PLAYER_JOINED_ROOM = "player_joined_room"
    PLAYER_LEFT_ROOM = "player_left_room"

    YOU_JOINED_THE_ROOM = "you_joined_the_room"
    YOU_LEFT_THE_ROOM = "you_left_the_room"

    GAME_STARTED = "game_started"
    GAME_ENDED = "game_ended"

    ROUND_STARTED = "round_started"
    PLAYER_SELECTED_CARD = "player_selected_card"
    PLAYER_CARD_REMOVED = "player_card_removed"
    ROUND_STATE_CHANGED = "round_state_changed"
    LEADER_HAS_CHOSEN_WINNER = "leader_has_chosen_winner"
    ROUND_ENDED = "round_ended"

    PLAYER_CARDS_UPDATED = "player_cards_updated"
