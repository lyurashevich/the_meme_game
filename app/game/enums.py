from enum import Enum


class RoomState(Enum):
    WAITING = "waiting"
    IN_PROGRESS = "in_progress"
    FULL = "full"


class GameState(Enum):
    STARTING = "starting"  # Game is about to start
    ACTIVE = "active"  # Game has started
    FINISHED = "finished"  # Game finished


class RoundState(Enum):
    CHOOSING_CARDS = "choosing_cards"  # Players choosing their cards
    LEADER_CHOOSING = "leader_choosing"  # Leader choosing winner
    ROUND_ENDED = "round_ended"  # Round finished


class WebsocketEvents(Enum):
    # replies to client actions
    ACK = "ack"
    ERROR = "error"

    # state: the client replaces what it has with what it receives
    SESSION = "session"  # who you are; sent on connect
    ROOMS_LIST = "rooms_list"  # for players outside rooms
    ROOM_STATE = "room_state"  # personal snapshot of your room

    # one-off moments that a snapshot can't express
    ROUND_WINNER = "round_winner"
    GAME_ENDED = "game_ended"
    CHAT_MESSAGE = "chat_message"
    YOU_LEFT_ROOM = "you_left_room"


class GameEndReason(Enum):
    OWNER_ENDED = "owner_ended"
    LIMIT_REACHED = "limit_reached"  # max_rounds or score_to_win
    NOT_ENOUGH_PLAYERS = "not_enough_players"
    OUT_OF_CARDS = "out_of_cards"
