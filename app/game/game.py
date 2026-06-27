import asyncio
import random
from asyncio import Task
from typing import Optional

from app.db import session_maker
from app.dependencies import game_manager, websocket_sender
from app.exceptions import (
    CardNotFoundException,
    InvalidGameStateException,
    InvalidPlayerActionException,
    InvalidRoundStateException,
    NotEnoughCardsException,
    NotEnoughPlayersException,
    PlayerNotFoundException,
    RoomNotFoundException,
    RoundNotFoundException,
)
from app.game.dataclasses import Game, GameRound, Room
from app.game.enums import GameState, RoundState
from app.game.game_settings import GameSettings
from app.models import SituationCard
from app.services.memes_services import CardService as MemeService
from app.services.situations_services import CardService as SituationService

MEME_CARDS_COOLDOWN = 20
SITUATION_CARDS_COOLDOWN = 30
CARDS_PER_PLAYER = 6


class GameLogic:
    def __init__(self):
        self.settings = GameSettings()
        self.game_manager = game_manager
        self.websocket_sender = websocket_sender

    async def phase_timer(self, room_id: str):

        # print(
        #     f"round state before timer: {self.get_game(room_id).current_round.state
        #     if self.get_game(room_id).current_round else None}")
        await asyncio.sleep(30)
        # print(f"Phase timeout for room {room_id}")

        async with game_manager.get_room_lock(room_id):
            game = game_manager.get_game(room_id)
            room = game_manager.get_room(room_id)

            if not game:
                return

            # Perform phase transition logic here, e.g.:
            if game.current_round:
                if game.current_round.state == RoundState.CHOOSING_CARDS:
                    game.current_round.state = RoundState.LEADER_CHOOSING

                    if self.websocket_sender is None:
                        raise RuntimeError("WebSocketSender not configured")

                    await self.websocket_sender.send_round_state_changed(room, RoundState.LEADER_CHOOSING.value)
                    print(f"round state after timer: {game.current_round.state}")
                elif game.current_round.state == RoundState.LEADER_CHOOSING:
                    game.current_round.state = RoundState.ROUND_ENDED

                    if self.websocket_sender is None:
                        raise RuntimeError("WebSocketSender not configured")

                    await self.websocket_sender.send_round_state_changed(room, RoundState.ROUND_ENDED.value)
                    await self.end_round(room_id)
                    print(f"round state after timer: {game.current_round.state}")
                else:
                    return  # No transition needed

    @staticmethod
    async def add_timer(room_id: str, name: str, task: Task) -> None:
        game_manager.room_tasks.setdefault(room_id, {})

        old_task = game_manager.room_tasks[room_id].get(name)
        if old_task and not old_task.done():
            old_task.cancel()

        game_manager.room_tasks[room_id][name] = task

    async def get_room(self, room_id) -> Room:
        if room_id not in self.game_manager.active_rooms:
            raise RoomNotFoundException()

        room = self.game_manager.active_rooms[room_id]
        return room

    @staticmethod
    async def validate_room_can_start_game(room: Room) -> None:
        if len(room.players) < 3:
            raise NotEnoughPlayersException()

    async def prepare_game(self, room_id: str) -> Game | None:

        async with self.game_manager.get_room_lock(room_id=room_id):
            room = await self.get_room(room_id)
            await self.validate_room_can_start_game(room)

            game = Game(room=room)

            game.leader_index = 0
            self.game_manager.active_games[room_id] = game

            await self.initialize_decks(game)

        return game

    async def start_first_round(self, room_id: str) -> Game:

        async with self.game_manager.get_room_lock(room_id):
            game = self.game_manager.get_game(room_id)

            if game.state != GameState.STARTING:
                raise InvalidGameStateException(game_state=GameState.STARTING.value)

            situation_card = await self.get_situation_card(game)
            await self.hand_out_initial_cards(game)
            new_round = GameRound(
                round_number=1,
                leader=game.room.owner,
                situation_card=situation_card,
                game=game,  # state = RoundState.CHOOSING_CARDS
            )
            game.current_round = new_round
            game.state = GameState.ACTIVE

            task = asyncio.create_task(self.phase_timer(room_id))

            await self.add_timer(room_id, "phase_timer", task)

        return game

    async def start_new_round(self, room_id: str):
        async with self.game_manager.get_room_lock(room_id):
            game = self.game_manager.get_game(room_id)

            prev_round = game.current_round

            if game.state != GameState.ACTIVE:
                raise InvalidGameStateException(game_state=GameState.ACTIVE.value)

            if prev_round.state != RoundState.ROUND_ENDED:
                raise InvalidRoundStateException(round_state=RoundState.ROUND_ENDED.value)

            situation_card = await self.get_situation_card(game)
            await self.hand_out_one_card(game)

            round_number = prev_round.round_number + 1
            new_leader = await self.choose_leader(game)

            new_round = GameRound(
                round_number=round_number,
                leader=new_leader,
                situation_card=situation_card,
                game=game,  # state = RoundState.CHOOSING_CARDS
            )
            game.current_round = new_round

    # todo: send a websocket event

    @staticmethod
    async def initialize_decks(game: Game) -> None:
        with session_maker() as db:
            game.meme_deck = list(MemeService(db).get_meme_cards())
            game.situation_deck = list(SituationService(db).get_situation_cards())

        random.shuffle(game.meme_deck)
        random.shuffle(game.situation_deck)

    @staticmethod
    async def hand_out_initial_cards(game: Game) -> None:

        if len(game.meme_deck) < len(game.room.players):
            raise NotEnoughCardsException()

        for player in game.room.players:
            for _ in range(CARDS_PER_PLAYER):
                if game.meme_deck:
                    card = game.meme_deck.pop(0)
                    player.handed_cards.append(card)

    @staticmethod
    async def hand_out_one_card(game: Game):

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
    async def get_situation_card(game: Game) -> SituationCard:
        if not game.situation_deck:
            raise NotEnoughCardsException()

        situation_card = random.choice(game.situation_deck)  # nosec B311 - game logic only, not cryptography
        game.situation_deck.remove(situation_card)

        return situation_card

    @staticmethod
    async def choose_leader(game: Game):
        game.leader_index = (game.leader_index + 1) % len(game.room.players)
        return game.room.players[game.leader_index]

    @staticmethod
    async def process_meme_deck(game):
        cards_to_return = game.meme_discard_pile.pop(game.current_round.round_number - MEME_CARDS_COOLDOWN, [])
        game.meme_deck.extend(cards_to_return)

    @staticmethod
    async def process_situation_deck(game):
        cards_to_return = game.situation_discard_pile.pop(
            game.current_round.round_number - SITUATION_CARDS_COOLDOWN, []
        )
        game.situation_deck.extend(cards_to_return)

    async def player_select_card(self, room_id: str, player_id: str, card_id: int):

        async with self.game_manager.get_room_lock(room_id):
            game = self.game_manager.get_game(room_id)

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

            if await self.validate_if_all_the_players_confirmed_their_choices():
                game.current_round.state = RoundState.LEADER_CHOOSING
                self.cancel_room_task(room_id, "phase_timer")

    async def validate_if_all_the_players_confirmed_their_choices(self):
        pass

    async def leader_choose_winner(self, room_id: str, card_id: int):

        async with self.game_manager.get_room_lock(room_id):
            game = self.game_manager.get_game(room_id)

            if not game.current_round:
                raise RoundNotFoundException()

            if game.state != GameState.ACTIVE:
                raise InvalidGameStateException(game_state=GameState.ACTIVE.value)

            if game.current_round.state != RoundState.LEADER_CHOOSING:
                raise InvalidRoundStateException(round_state=RoundState.LEADER_CHOOSING.value)

            winner_player_id = next(
                (player_id for player_id, card in game.current_round.player_choices.items() if card.id == card_id), None
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

            game.current_round.state = RoundState.ROUND_ENDED
            game.current_round.finalized = True
            print(f"round state changed in leader_choose_winner: {game.current_round.state}")
            self.cancel_room_task(room_id, "phase_timer")

        await self.end_round(room_id)

    def cancel_room_task(self, room_id: str, task_name: str) -> None:
        tasks = self.game_manager.room_tasks.get(room_id, {})
        phase_task = tasks.pop(task_name, None)
        if phase_task:
            phase_task.cancel()
            print("task cancelled")

    async def end_round(self, room_id: str):  # todo: change name to FINALIZE_ROUND
        async with self.game_manager.get_room_lock(room_id):
            game = self.game_manager.get_game(room_id)

            if game.state != GameState.ACTIVE:
                raise InvalidGameStateException(game_state=GameState.ACTIVE.value)

            if not game.current_round:
                raise RoundNotFoundException()

            if game.current_round.state != RoundState.ROUND_ENDED:
                raise InvalidRoundStateException(round_state=RoundState.ROUND_ENDED.value)

            round_data = game.current_round

            for player_id, card in round_data.player_choices.items():  # {int: MemeCard}
                game.meme_discard_pile.setdefault(game.current_round.round_number, []).append(card)

            if round_data.situation_card:
                game.situation_discard_pile.setdefault(game.current_round.round_number, []).append(
                    round_data.situation_card
                )

            await self.process_meme_deck(game)
            await self.process_situation_deck(game)

        await self.start_new_round(room_id)

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

    def get_game_state(self, room_id: str) -> Optional[Game]:
        with self.game_manager.get_room_lock(room_id):
            game = self.game_manager.get_game(room_id)
        return game

    def get_room_state(self, room_id: str) -> Optional[Room]:
        with self.game_manager.get_room_lock(room_id):
            room = self.game_manager.get_room(room_id)
        return room


game_logic = GameLogic()
