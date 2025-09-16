import asyncio
import random
from datetime import datetime
from typing import Optional

from app.game.dataclasses import Game, GameRound, Room
from app.game.enums import GameState, RoundState
from app.game.game_manager import game_manager
from app.game.game_settings import GameSettings
from app.models import SituationCard
from app.services.memes_services import CardService as MemeService
from app.services.situations_services import CardService as SituationService


class GameLogic:
    def __init__(self):
        # self.game_manager = GameManager()
        self.settings = GameSettings()

    async def start_game(self, room_id: str) -> Game:
        if room_id not in game_manager.active_rooms:
            raise Exception("Room not found")

        room = game_manager.active_rooms[room_id]

        if len(room.players) < 3:
            raise Exception(
                "Not enough players to start game. You need at least 3 players."
            )

        game = Game(room=room, state=GameState.STARTING)

        await self.initialize_decks(game)
        await self.hand_out_initial_cards(game)
        game.leader_index = 0
        await self.start_new_round(game)
        game_manager.active_games[room_id] = game

        return game

    @staticmethod
    async def initialize_decks(game: Game) -> None:
        game.meme_deck = MemeService.MEME_CARDS
        game.situation_deck = SituationService.SITUATION_CARDS

        random.shuffle(game.meme_deck)
        random.shuffle(game.situation_deck)

    async def hand_out_initial_cards(self, game: Game) -> None:
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

        return random.choice(game.situation_deck)

    @staticmethod
    async def choose_leader(game: Game):
        game.leader_index = (game.leader_index + 1) % len(game.room.players)
        return game.room.players[game.leader_index]

    async def start_new_round(self, game: Game) -> None:
        if game.state == GameState.WAITING:
            game.state = GameState.IN_PROGRESS

        game.round_number += 1
        if game.round_number != 1:
            await self.hand_out_one_card(game)

        current_leader = game.room.players[game.leader_index]

        situation_card = await self.get_situation_card(game=game)

        game.current_round = GameRound(
            round_number=game.round_number,
            leader=current_leader,
            situation_card=situation_card,
        )

        game.state = GameState.ROUND_ACTIVE

    @staticmethod
    async def process_meme_deck(game):
        cards_to_return = game.meme_discard_pile.pop(
            game.current_round - 10, []
        )
        game.meme_deck.extend(cards_to_return)

    @staticmethod
    async def process_situation_deck(game):
        cards_to_return = game.situation_discard_pile.pop(game.round_number - 20, [])
        game.situation_deck.extend(cards_to_return)

    async def player_select_card(
        self, game: Game, player_id: int, card_id: int
    ) -> bool:
        """Player selects a card for the current round"""
        if (
            not game.current_round
            or game.current_round.state != RoundState.CHOOSING_CARDS
        ):
            return False

        player = next((p for p in game.room.players if p.id == player_id), None)
        if not player or player == game.current_round.leader:
            return False

        # Find the card in player's hand
        selected_card = next((c for c in player.handed_cards if c.id == card_id), None)
        if not selected_card:
            return False

        # Record the choice
        game.current_round.player_choices[player_id] = selected_card
        player.selected_card = selected_card

        # Check if all players have chosen
        non_leader_players = [
            p for p in game.room.players if p != game.current_round.leader
        ]
        if len(game.current_round.player_choices) >= len(non_leader_players):
            await self.end_card_selection_phase(game)

        return True

    async def end_card_selection_phase(self, game: Game):
        """End the card selection phase and move to leader choosing"""
        if not game.current_round:
            return

        game.current_round.state = RoundState.LEADER_CHOOSING
        game.state = GameState.ROUND_ENDING

    async def leader_choose_winner(self, game: Game, winner_player_id: int) -> bool:
        """Leader chooses the winner of the round"""
        if (
            not game.current_round
            or game.current_round.state != RoundState.LEADER_CHOOSING
        ):
            return False

        winner = next((p for p in game.room.players if p.id == winner_player_id), None)
        if not winner or winner == game.current_round.leader:
            return False

        # Set winner and award point
        game.current_round.winner = winner
        winner.score += 1

        # End the round
        await self.end_round(game)
        return True

    async def end_round(self, game: Game):
        if not game.current_round:
            raise Exception("Game not found")

        round_data = game.current_round
        round_data.state = RoundState.ROUND_ENDED
        round_data.end_time = datetime.now()

        for (
            player_id,
            card,
        ) in round_data.player_choices.items():  # {int: list[MemeCard]}
            if not game.meme_discard_pile[game.round_number]:
                game.meme_discard_pile[game.round_number] = []
            game.meme_discard_pile[game.round_number].append(card)

            player = next((p for p in game.room.players if p.id == player_id), None)
            if player:
                player.handed_cards.remove(card)
                player.selected_card = None

        if round_data.situation_card:
            game.situation_discard_pile[game.round_number] = round_data.situation_card

        # Check if game should end
        if await self.should_end_game(game):
            await self.end_game(game)
        else:
            # Choose next leader and start new round
            await self.choose_leader(game)
            await self.start_new_round(game)

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

    async def delayed_cleanup(self, room_id: str, delay_seconds: int = 30):
        """Clean up room and game after delay"""
        await asyncio.sleep(delay_seconds)
        await self.cleanup_room(room_id)

    def get_game_state(self, room_id: str) -> Optional[Game]:
        """Get current game state for a room"""
        return self.game_manager.active_games.get(room_id)

    def get_room_state(self, room_id: str) -> Optional[Room]:
        """Get current room state"""
        return self.game_manager.active_rooms.get(room_id)
