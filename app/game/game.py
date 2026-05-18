import random
from typing import Optional

from app.game.dataclasses import Game, GameRound, Room
from app.game.enums import GameState, RoundState
from app.game.game_manager import get_game_manager
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
        self.game_manager = get_game_manager()

    async def get_room(self, room_id) -> Room:
        if room_id not in self.game_manager.active_rooms:
            raise Exception("Room not found")

        room = self.game_manager.active_rooms[room_id]
        return room

    @staticmethod
    async def validate_room_can_start_game(room: Room) -> None:
        if len(room.players) < 3:
            raise Exception("Not enough players to start game. You need at least 3 players.")

    async def prepare_game(self, room_id: str) -> Game | None:

        async with self.game_manager.get_room_lock(room_id=room_id):
            room = await self.get_room(room_id)
            await self.validate_room_can_start_game(room)

            game = Game(room=room)

            game.leader_index = 0
            self.game_manager.active_games[room_id] = game

        await self.initialize_decks(game)

        return game

    async def start_first_round(self, game):
        if game.state != GameState.STARTING:
            raise Exception("Cannot start first round: game is not in STARTING state")

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
        return game

    async def start_new_round(self, game: Game):
        async with self.game_manager.get_room_lock(game.room.id):

            if (
                not game.current_round
                or game.state != GameState.ACTIVE
                or game.current_round.state != RoundState.ROUND_ENDED
            ):
                raise Exception("Cannot start new round: game is not in ACTIVE state or round has not ended")

            situation_card = await self.get_situation_card(game)
            await self.hand_out_one_card(game)
            round_number = game.current_round.round_number + 1
            new_leader = await self.choose_leader(game)
            new_round = GameRound(
                round_number=round_number,
                leader=new_leader,
                situation_card=situation_card,
                game=game,  # state = RoundState.CHOOSING_CARDS
            )
            game.current_round = new_round

    @staticmethod
    async def initialize_decks(game: Game) -> None:
        game.meme_deck = MemeService.MEME_CARDS.copy()
        game.situation_deck = SituationService.SITUATION_CARDS.copy()

        random.shuffle(game.meme_deck)
        random.shuffle(game.situation_deck)

    @staticmethod
    async def hand_out_initial_cards(game: Game) -> None:

        if len(game.meme_deck) < len(game.room.players):
            raise Exception("Not enough memes in deck")

        for player in game.room.players:
            for _ in range(CARDS_PER_PLAYER):
                if game.meme_deck:
                    card = game.meme_deck.pop(0)
                    player.handed_cards.append(card)

    @staticmethod
    async def hand_out_one_card(game: Game):

        if (
            not game.current_round
            or game.state != GameState.ACTIVE
            or game.current_round.state != RoundState.ROUND_ENDED
        ):
            raise Exception("Cannot start new round: game is not in ACTIVE state or round has not ended")

        current_leader = game.room.players[game.leader_index]

        if not game.meme_deck:
            raise Exception("You have run out of cards(((")

        for player in game.room.players:
            if player == current_leader:
                continue
            card = game.meme_deck.pop(0)
            player.handed_cards.append(card)

    @staticmethod
    async def get_situation_card(game: Game) -> SituationCard:
        if not game.situation_deck:
            raise Exception("No situation cards available")

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

    async def player_select_card(self, game: Game, player_id: str, card_id: int):

        if (
            not game.current_round
            or game.current_round.state != RoundState.CHOOSING_CARDS
            or game.state != GameState.ACTIVE
        ):
            raise Exception(
                "Error: game is not ACTIVE state of round is missing or round is not in CHOOSING_CARDS state"
            )

        player = next((player for player in game.room.players if player.id == player_id), None)
        if not player:
            raise Exception("Player not found")
        if player == game.current_round.leader:
            raise Exception("Leader cannot choose card")
        if player_id in game.current_round.player_choices:
            raise Exception("Player already selected a card")

        selected_card = next((card for card in player.handed_cards if card.id == card_id), None)
        if not selected_card:
            raise Exception("Card not found")

        game.current_round.player_choices[player_id] = selected_card
        player.handed_cards.remove(selected_card)

    async def leader_choose_winner(self, game: Game, winner_player_id: str):

        if (
            not game
            or not game.current_round
            or game.current_round.state != RoundState.LEADER_CHOOSING
            or game.state != GameState.ACTIVE
        ):
            raise Exception(
                "Error: game is not ACTIVE state of round is missing or round is not in LEADER_CHOOSING state"
            )

        winner = next((p for p in game.room.players if p.id == winner_player_id), None)
        if not winner:
            raise Exception("Player not found")

        if winner == game.current_round.leader:
            raise Exception("Leader cannot be a winner")

        if winner_player_id not in game.current_round.player_choices:
            raise Exception("Player did not submit a card")

        game.current_round.winner = winner
        winner.score += 1

    async def end_round(self, game: Game):
        async with self.game_manager.get_room_lock(game.room.id):

            if (
                not game.current_round
                or game.current_round.state != RoundState.LEADER_CHOOSING
                or game.state != GameState.ACTIVE
            ):
                raise Exception(
                    "Error: game is not ACTIVE state of round is missing or round is not in LEADER_CHOOSING state"
                )

            round_data = game.current_round
            round_data.state = RoundState.ROUND_ENDED

            for player_id, card in round_data.player_choices.items():  # {int: MemeCard}
                game.meme_discard_pile.setdefault(game.current_round.round_number, []).append(card)

            if round_data.situation_card:
                game.situation_discard_pile.setdefault(game.current_round.round_number, []).append(
                    round_data.situation_card
                )

        await self.process_meme_deck(game)
        await self.process_situation_deck(game)

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
        """Get current game state for a room"""
        return self.game_manager.active_games.get(room_id)

    def get_room_state(self, room_id: str) -> Optional[Room]:
        """Get current room state"""
        return self.game_manager.active_rooms.get(room_id)


game_logic = GameLogic()
