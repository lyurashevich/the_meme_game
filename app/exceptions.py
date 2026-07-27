class CustomException(Exception):
    code: str = "custom_exception"
    status_code: int = 400
    message: str = ""


class GameNotFoundException(CustomException):
    code: str = "game_not_found"
    status_code: int = 404
    message: str = "Game not found"


class PlayerNotFoundException(CustomException):
    code: str = "player_not_found"
    status_code: int = 404
    message: str = "Player not found"


class RoomNotFoundException(CustomException):
    code: str = "room_not_found"
    status_code: int = 404
    message: str = "Room not found"


class RoundNotFoundException(CustomException):
    code: str = "round_not_found"
    status_code: int = 404
    message: str = "Round not found"


class InvalidGameStateException(CustomException):
    code: str = "invalid_game_state"
    status_code: int = 400

    def __init__(self, game_state: str):
        self.message: str = f"Invalid game state. Game state must be {game_state} to perform this action"

        super().__init__(self.message)


class InvalidRoundStateException(CustomException):
    code: str = "invalid_round_state"
    status_code: int = 400

    def __init__(self, round_state: str):
        self.message: str = f"Invalid round state. Round state must be {round_state} to perform this action"

        super().__init__(self.message)


class InvalidPlayerActionException(CustomException):
    code: str = "invalid_player_action"
    status_code: int = 400

    def __init__(self, hint: str):
        self.message: str = f"Invalid player action. {hint}"

        super().__init__(self.message)


class CardNotFoundException(CustomException):
    code: str = "card_not_found"
    status_code: int = 404
    message: str = "Card not found"


class NotEnoughPlayersException(CustomException):
    code: str = "not_enough_players"
    status_code: int = 400
    message: str = "Not enough players to start game. You need at least 3 players."


class NotEnoughCardsException(CustomException):
    code: str = "not_enough_cards"
    status_code: int = 400
    message: str = "Not enough cards to start game."


class InvalidReconnectToken(CustomException):
    code: str = "invalid_reconnect_token"
    status_code: int = 400
    message: str = "Invalid reconnect token"


class AlreadyInARoomException(CustomException):
    code: str = "already_in_a_room"
    status_code = 400
    message: str = "You have already joined another room"


class PlayerNotInRoomException(CustomException):
    code: str = "player_not_in_room"
    status_code: int = 409
    message: str = "Player is not in the room"


class NotRoomOwnerException(CustomException):
    code: str = "not_room_owner_exception"
    status_code: int = 403
    message: str = "This action is allowed for the room owner"
