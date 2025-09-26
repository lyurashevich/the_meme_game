import asyncio
import random
from datetime import datetime
from typing import Optional

from app.game.dataclasses import Game, GameRound, Room
from app.game.enums import GameState, RoundState
from app.game.game_manager import get_game_manager
from app.game.game_settings import GameSettings
from app.models import SituationCard
from app.services.memes_services import CardService as MemeService
from app.services.situations_services import CardService as SituationService


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

        room = await self.get_room(room_id)
        await self.validate_room_can_start_game(room)

        game = Game(room=room, state=GameState.STARTING)

        await self.initialize_decks(game)
        game.leader_index = 0
        self.game_manager.active_games[room_id] = game

        return game

    async def start_first_round(self, game):
        situation_card = await self.get_situation_card(game)
        await self.hand_out_initial_cards(game)
        new_round = GameRound(
            round_number=1,
            leader=game.room.owner,
            situation_card=situation_card,
            game=game,
        )
        game.current_round = new_round
        return new_round

    async def start_new_round(self, game):
        situation_card = await self.get_situation_card(game)
        await self.hand_out_one_card(game)
        round_number = game.current_round.round_number + 1
        new_leader = await self.choose_leader(game)
        new_round = GameRound(
            round_number=round_number,
            leader=new_leader,
            situation_card=situation_card,
            game=game,
        )
        game.current_round = new_round

    @staticmethod
    async def initialize_decks(game: Game) -> None:
        game.meme_deck = MemeService.MEME_CARDS.copy()
        game.situation_deck = SituationService.SITUATION_CARDS

        random.shuffle(game.meme_deck)
        random.shuffle(game.situation_deck)

    async def hand_out_initial_cards(self, game: Game) -> None:

        if len(game.meme_deck) < len(game.room.players):
            raise Exception("Not enough memes in deck")

        for player in game.room.players:
            for _ in range(self.settings.cards_per_player):
                if game.meme_deck:
                    card = game.meme_deck.pop(0)
                    player.handed_cards.append(card)

    @staticmethod
    async def hand_out_one_card(game: Game):
        current_leader = game.room.players[game.leader_index]

        if not game.meme_deck:
            raise Exception("You have run out of cards(((")

        for player in game.room.players:
            if player == current_leader:
                continue
            card = game.meme_deck.pop(0)
            player.handed_cards.append(card)

    @staticmethod
    async def get_situation_card(game: Game) -> Optional[SituationCard]:
        if not game.situation_deck:
            raise Exception("No situation cards available")

        situation_card = random.choice(game.situation_deck)
        game.situation_deck.remove(situation_card)

        return situation_card

    @staticmethod
    async def choose_leader(game: Game):
        game.leader_index = (game.leader_index + 1) % len(game.room.players)
        return game.room.players[game.leader_index]

    async def process_meme_deck(self, game):
        cards_to_return = game.meme_discard_pile.pop(
            game.current_round.round_number - self.settings.meme_card_cooldown, []
        )
        game.meme_deck.extend(cards_to_return)

    async def process_situation_deck(self, game):
        cards_to_return = game.situation_discard_pile.pop(
            game.current_round.round_number - self.settings.situation_card_cooldown, []
        )
        game.situation_deck.extend(cards_to_return)

    async def player_select_card(self, game: Game, player_id: int, card_id: int):
        if not game.current_round or game.current_round.state != RoundState.CHOOSING_CARDS:
            return

        player = next((player for player in game.room.players if player.id == player_id), None)
        if not player or player == game.current_round.leader:
            return

        selected_card = next((card for card in player.handed_cards if card.id == card_id), None)
        if not selected_card:
            return

        game.current_round.player_choices[player_id] = selected_card

        non_leader_players = [player for player in game.room.players if player != game.current_round.leader]
        if len(game.current_round.player_choices) >= len(non_leader_players):
            await self.end_card_selection_phase(game)

    async def end_card_selection_phase(self, game: Game):
        """End the card selection phase and move to leader choosing"""
        if not game.current_round:
            return

        game.current_round.state = RoundState.LEADER_CHOOSING
        game.state = GameState.ROUND_ENDING

    async def leader_choose_winner(self, game: Game, winner_player_id: int):
        """Leader chooses the winner of the round"""
        if not game.current_round or game.current_round.state != RoundState.LEADER_CHOOSING:
            return

        winner = next((p for p in game.room.players if p.id == winner_player_id), None)
        if not winner or winner == game.current_round.leader:
            return

        # Set winner and award point
        game.current_round.winner = winner
        winner.score += 1

        # End the round
        # await self.end_round(game)
        # return True

    async def end_round(self, game: Game):
        if not game.current_round:
            raise Exception("Game not found")

        round_data = game.current_round
        round_data.state = RoundState.ROUND_ENDED
        round_data.end_time = datetime.now()

        for player_id, card in round_data.player_choices.items():  # {int: MemeCard}
            game.meme_discard_pile.setdefault(game.current_round.round_number, []).append(card)

            player = next((player for player in game.room.players if player.id == player_id), None)
            if player:
                player.handed_cards.remove(card)
                player.selected_card = None

        if round_data.situation_card:
            game.situation_discard_pile[game.current_round.round_number] = round_data.situation_card

        # Check if game should end
        if await self.should_end_game(game):
            await self.end_game(game)
        # else:
        #     # Choose next leader and start new round
        #     await self.choose_leader(game)
        #     await self.start_new_round(game)

        await self.process_meme_deck(game)
        await self.process_situation_deck(game)

    async def should_end_game(self, game: Game) -> bool:
        """Check if the game should end"""
        # Check if any player has reached the score limit
        if self.settings.score_to_win:
            for player in game.room.players:
                if player.score >= self.settings.score_to_win:
                    return True

        # Check if max rounds reached
        if self.settings.max_rounds and game.round_number >= self.settings.max_rounds:
            return True

        return False

    async def end_game(self, game: Game):
        """End the game and clean up"""
        game.state = GameState.FINISHED
        game.ended_at = datetime.now()

        # Clean up after a delay to allow players to see final scores
        asyncio.create_task(self.delayed_cleanup(game.room.id, delay_seconds=30))

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
