import asyncio
import random
from asyncio import Task
from typing import Optional

from app.db import session_maker
from app.exceptions import (
    CardNotFoundException,
    InvalidGameStateException,
    InvalidPlayerActionException,
    InvalidRoundStateException,
    NotEnoughCardsException,
    NotEnoughPlayersException,
    PlayerNotFoundException,
    RoundNotFoundException,
)
from app.game.connection_manager import ConnectionManager
from app.game.dataclasses import Game, GameRound, Room
from app.game.enums import GameState, RoundState, WebsocketEvents
from app.game.game_manager import GameManager
from app.game.game_settings import GameSettings
from app.models import SituationCard
from app.schemas.game import GameScore
from app.services.memes_services import CardService as MemeService
from app.services.room_service import RoomService
from app.services.situations_services import CardService as SituationService

MEME_CARDS_COOLDOWN = 20
SITUATION_CARDS_COOLDOWN = 30
CARDS_PER_PLAYER = 6


class GameService:
    def __init__(
        self,
        room_service: RoomService,
        game_manager: GameManager,
        connection_manager: ConnectionManager,
    ):
        self.room_service = room_service
        self.game_manager = game_manager
        self.connection_manager = connection_manager

    async def finish_round_flow(self, room_id: str) -> None:
        async with self.room_service.get_room_lock(room_id):
            game = self.game_manager.get_game(room_id)
            await self._finalize_round(game)

            game = self.game_manager.get_game(room_id)
            await self._start_new_round(game)

        await self.connection_manager.broadcast_to_players(
            [player.id for player in self.room_service.get_room(room_id).players],
            {"event": WebsocketEvents.ROUND_STATE_CHANGED.value, "payload": {"state": RoundState.ROUND_ENDED.value}},
        )
        await self.connection_manager.broadcast_to_players(
            [player.id for player in self.room_service.get_room(room_id).players],
            {"event": WebsocketEvents.ROUND_STATE_CHANGED.value, "payload": {"state": RoundState.CHOOSING_CARDS.value}},
        )

    @staticmethod
    def _change_round_state(current_round: GameRound, new_state: RoundState) -> bool:

        if current_round.state == new_state:
            return False

        current_round.state = new_state
        print(f"round phase has changed to {new_state.value.upper()}")
        return True

    async def phase_timer(self, room_id: str):
        round_state_changed = False
        finish_round = False
        room = None

        await asyncio.sleep(GameSettings.round_time_limit)  # 60 seconds

        async with self.room_service.get_room_lock(room_id):
            game = self.game_manager.get_game(room_id)
            room = self.room_service.get_room(room_id)

            if not game or not game.current_round:
                return

            if game.current_round.state == RoundState.CHOOSING_CARDS:
                round_state_changed = self._change_round_state(game.current_round, RoundState.LEADER_CHOOSING)
            elif game.current_round.state == RoundState.LEADER_CHOOSING:
                finish_round = True

        if round_state_changed:
            await self.connection_manager.broadcast_to_players(
                [player.id for player in room.players],
                {
                    "event": WebsocketEvents.ROUND_STATE_CHANGED.value,
                    "payload": {"state": RoundState.LEADER_CHOOSING.value},
                },
            )

        if finish_round:
            await self.finish_round_flow(room_id)

    async def get_game_score(self, room_id: str) -> list[GameScore]:
        async with self.room_service.get_room_lock(room_id):
            game = self.game_manager.get_game(room_id)

            return [
                GameScore(id=player.id, username=player.username, score=player.score) for player in game.room.players
            ]

    async def add_timer(self, room_id: str, name: str, task: Task) -> None:
        self.game_manager.room_tasks.setdefault(room_id, {})

        old_task = self.game_manager.room_tasks[room_id].get(name)
        if old_task and not old_task.done():
            old_task.cancel()

        self.game_manager.room_tasks[room_id][name] = task

    @staticmethod
    def _validate_room_can_start_game(room: Room) -> None:
        if len(room.players) < 3:
            raise NotEnoughPlayersException()

    async def prepare_game(self, room_id: str) -> Game | None:

        async with self.room_service.get_room_lock(room_id=room_id):
            room = self.room_service.get_room(room_id)
            self._validate_room_can_start_game(room)

            game = Game(room=room)

            game.leader_index = 0
            self.game_manager.active_games[room_id] = game

            await self._initialize_decks(game)

        return game

    async def start_first_round(self, room_id: str) -> Game:

        async with self.room_service.get_room_lock(room_id):
            game = self.game_manager.get_game(room_id)

            if game.state != GameState.STARTING:
                raise InvalidGameStateException(game_state=GameState.STARTING.value)

            situation_card = await self._get_situation_card(game)
            await self._hand_out_initial_cards(game)
            new_round = GameRound(
                round_number=1,
                leader=game.room.owner,  # type: ignore
                situation_card=situation_card,
                game=game,  # state = RoundState.CHOOSING_CARDS
            )
            game.current_round = new_round
            game.state = GameState.ACTIVE

            task = asyncio.create_task(self.phase_timer(room_id))

            await self.add_timer(room_id, "phase_timer", task)

        return game

    async def _start_new_round(self, game: Game):
        prev_round = game.current_round

        if game.state != GameState.ACTIVE:
            raise InvalidGameStateException(game_state=GameState.ACTIVE.value)

        if prev_round.state != RoundState.ROUND_ENDED:  # type: ignore
            raise InvalidRoundStateException(round_state=RoundState.ROUND_ENDED.value)

        situation_card = await self._get_situation_card(game)
        await self._hand_out_one_card(game)

        round_number = prev_round.round_number + 1  # type: ignore
        new_leader = await self._choose_leader(game)

        new_round = GameRound(
            round_number=round_number,
            leader=new_leader,
            situation_card=situation_card,
            game=game,  # state = RoundState.CHOOSING_CARDS
        )
        game.current_round = new_round

    # todo: send a websocket event

    @staticmethod
    async def _initialize_decks(game: Game) -> None:
        with session_maker() as db:
            game.meme_deck = list(MemeService(db).get_meme_cards())
            game.situation_deck = list(SituationService(db).get_situation_cards())

        random.shuffle(game.meme_deck)
        random.shuffle(game.situation_deck)

    @staticmethod
    async def _hand_out_initial_cards(game: Game) -> None:

        if len(game.meme_deck) < len(game.room.players):
            raise NotEnoughCardsException()

        for player in game.room.players:
            for _ in range(CARDS_PER_PLAYER):
                if game.meme_deck:
                    card = game.meme_deck.pop(0)
                    player.handed_cards.append(card)

    @staticmethod
    async def _hand_out_one_card(game: Game):

        if not game.current_round:
            raise RoundNotFoundException()

        if game.state != GameState.ACTIVE:
            raise InvalidGameStateException(game_state=GameState.ACTIVE.value)

        if game.current_round.state != RoundState.ROUND_ENDED:
            raise InvalidRoundStateException(round_state=RoundState.ROUND_ENDED.value)

        current_leader = game.room.players[game.leader_index]

        if not game.meme_deck:
            raise NotEnoughCardsException()

        for player in game.room.players:
            if player == current_leader:
                continue
            card = game.meme_deck.pop(0)
            player.handed_cards.append(card)

    @staticmethod
    async def _get_situation_card(game: Game) -> SituationCard:
        if not game.situation_deck:
            raise NotEnoughCardsException()

        situation_card = random.choice(game.situation_deck)  # nosec B311 - game logic only, not cryptography
        game.situation_deck.remove(situation_card)

        return situation_card

    @staticmethod
    async def _choose_leader(game: Game):
        game.leader_index = (game.leader_index + 1) % len(game.room.players)
        return game.room.players[game.leader_index]

    @staticmethod
    async def _process_meme_deck(game):
        cards_to_return = game.meme_discard_pile.pop(game.current_round.round_number - MEME_CARDS_COOLDOWN, [])
        game.meme_deck.extend(cards_to_return)

    @staticmethod
    async def _process_situation_deck(game):
        cards_to_return = game.situation_discard_pile.pop(
            game.current_round.round_number - SITUATION_CARDS_COOLDOWN, []
        )
        game.situation_deck.extend(cards_to_return)

    async def player_select_card(self, room_id: str, player_id: str, card_id: int) -> None:
        round_state_changed = False

        async with self.room_service.get_room_lock(room_id):
            game = self.game_manager.get_game(room_id)
            room = self.room_service.get_room(room_id)

            if not game.current_round:
                raise RoundNotFoundException()

            if game.current_round.state != RoundState.CHOOSING_CARDS:
                raise InvalidRoundStateException(round_state=RoundState.CHOOSING_CARDS.value)

            if game.state != GameState.ACTIVE:
                raise InvalidGameStateException(game_state=GameState.ACTIVE.value)

            player = next((player for player in game.room.players if player.id == player_id), None)
            if not player:
                raise PlayerNotFoundException()
            if player == game.current_round.leader:
                raise InvalidPlayerActionException(hint="Leader cannot choose a card")
            if player_id in game.current_round.player_choices:
                raise InvalidPlayerActionException(hint="Player already selected a card")

            selected_card = next((card for card in player.handed_cards if card.id == card_id), None)
            if not selected_card:
                raise CardNotFoundException()

            game.current_round.player_choices[player_id] = selected_card
            player.handed_cards.remove(selected_card)

            if self._validate_if_all_the_players_confirmed_their_choices(game):
                round_state_changed = self._change_round_state(game.current_round, RoundState.LEADER_CHOOSING)
                if round_state_changed:
                    self._cancel_room_task(room_id, "phase_timer")

        if round_state_changed:
            await self.connection_manager.broadcast_to_players(
                [player.id for player in room.players],
                {
                    "event": WebsocketEvents.ROUND_STATE_CHANGED.value,
                    "payload": {"state": RoundState.LEADER_CHOOSING.value, "expected_cards": len(room.players) - 1},
                },
            )

    @staticmethod
    def _validate_if_all_the_players_confirmed_their_choices(game: Game) -> bool:
        return (
            len(game.current_round.player_choices) == len(game.room.players) - 1
            if game and game.current_round
            else False
        )

    async def leader_choose_winner(self, room_id: str, card_id: int):

        async with self.room_service.get_room_lock(room_id):
            game = self.game_manager.get_game(room_id)

            if not game.current_round:
                raise RoundNotFoundException()

            if game.state != GameState.ACTIVE:
                raise InvalidGameStateException(game_state=GameState.ACTIVE.value)

            if game.current_round.state != RoundState.LEADER_CHOOSING:
                raise InvalidRoundStateException(round_state=RoundState.LEADER_CHOOSING.value)

            winner_player_id = next(
                (player_id for player_id, card in game.current_round.player_choices.items() if card.id == card_id),
                None,
            )

            winner = next((p for p in game.room.players if p.id == winner_player_id), None)
            if not winner:
                raise PlayerNotFoundException()

            if winner == game.current_round.leader:
                raise InvalidPlayerActionException(hint="Leader cannot be a winner")

            if winner_player_id not in game.current_round.player_choices:
                raise InvalidPlayerActionException(hint="Winner must be selected from the players who submitted cards")

            game.current_round.winner = winner
            winner.score += 1

        await self.finish_round_flow(room_id)

        await self.connection_manager.broadcast_to_players(
            [player.id for player in self.room_service.get_room(room_id).players],
            {
                "event": WebsocketEvents.ROUND_STATE_CHANGED.value,
                "payload": {"state": RoundState.ROUND_ENDED.value},
            },
        )

    def _cancel_room_task(self, room_id: str, task_name: str) -> None:
        tasks = self.game_manager.room_tasks.get(room_id, {})
        phase_task = tasks.pop(task_name, None)
        if phase_task:
            phase_task.cancel()
            print("task cancelled")

    async def _finalize_round(self, game: Game):
        if game.state != GameState.ACTIVE:
            raise InvalidGameStateException(game_state=GameState.ACTIVE.value)

        if not game.current_round:
            raise RoundNotFoundException()

        round_data = game.current_round

        self._change_round_state(round_data, RoundState.ROUND_ENDED)
        for player_id, card in round_data.player_choices.items():  # {int: MemeCard}
            game.meme_discard_pile.setdefault(game.current_round.round_number, []).append(card)

        if round_data.situation_card:
            game.situation_discard_pile.setdefault(game.current_round.round_number, []).append(
                round_data.situation_card
            )

        game.current_round.finalized = True
        self._cancel_room_task(game.room_id, "phase_timer")

        await self._process_meme_deck(game)
        await self._process_situation_deck(game)

    # async def end_game(self, game: Game):
    #     """End the game and clean up"""
    #     game.state = GameState.FINISHED
    #     game.ended_at = datetime.now()
    #
    #     # Clean up after a delay to allow players to see final scores
    #     asyncio.create_task(self.delayed_cleanup(game.room.id, delay_seconds=30))

    # async def delayed_cleanup(self, room_id: str, delay_seconds: int = 30):
    #     """Clean up room and game after delay"""
    #     await asyncio.sleep(delay_seconds)
    #     await self.cleanup_room(room_id)

    async def get_game_state(self, room_id: str) -> Optional[Game]:
        async with self.room_service.get_room_lock(room_id):
            game = self.game_manager.get_game(room_id)
        return game

    async def get_room_state(self, room_id: str) -> Optional[Room]:
        async with self.room_service.get_room_lock(room_id):
            room = self.room_service.get_room(room_id)
        return room
