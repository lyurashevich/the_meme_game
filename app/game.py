import asyncio
import random
from datetime import datetime, timedelta
from re import S
from typing import Dict, List, Optional

from models import (Game, GameManager, GameRound, GameSettings, GameState,
                    MemeCard, Player, Room, RoundState, SituationCard)


class GameLogic:
    def __init__(self):
        self.game_manager = GameManager()
        self.settings = GameSettings()

    async def generate_invitation_link(self, room_id: str) -> str:
        """Generate an invitation link for a room"""
        return f"https://your-domain.com/join/{room_id}"

    async def create_room(
        self, room_name: str, max_players: int = 10, is_private: bool = False
    ) -> Room:
        """Create a new room"""
        room = Room(name=room_name, max_players=max_players, is_private=is_private)
        if room.is_private:
            await self.generate_invitation_link(room.id)

        self.game_manager.active_rooms[room.id] = room
        return room

    async def join_room(self, room_id: str, player: Player) -> bool:
        """Add player to room with username uniqueness validation"""
        if room_id not in self.game_manager.active_rooms:
            raise Exception("Room not found")

        room = self.game_manager.active_rooms[room_id]

        # Check if room is full
        if len(room.players) >= room.max_players:
            raise Exception("Room is full")

        # Check username uniqueness within the room
        for existing_player in room.players:
            if existing_player.username.lower() == player.username.lower():
                raise Exception("Username already exists")

        # Set connection order for leader rotation
        player.connection_order = len(room.players)

        # First player becomes owner and host
        if not room.players:
            room.owner = player
            player.is_host = True

        room.players.append(player)
        self.game_manager.player_connections[player.id] = room_id
        return True

    async def leave_room(self, player_id: int) -> bool:
        """Remove player from room"""
        if player_id not in self.game_manager.player_connections:
            raise Exception("Player not found")

        room_id = self.game_manager.player_connections[player_id]
        if room_id not in self.game_manager.active_rooms:
            raise Exception("Room not found")

        room = self.game_manager.active_rooms[room_id]
        player = next((p for p in room.players if p.id == player_id), None)

        if not player:
            raise Exception("Player not found")

        room.players.remove(player)
        del self.game_manager.player_connections[player_id]

        # If no players left, clean up room and game
        if not room.players:
            await self.cleanup_room(room_id)

        return True

    async def start_game(self, room_id: str) -> bool:
        """Start a new game in the room"""
        if room_id not in self.game_manager.active_rooms:
            raise Exception("Room not found")

        room = self.game_manager.active_rooms[room_id]

        # Need at least 3 players to start
        if len(room.players) < 3:
            raise Exception(
                "Not enough players to start game. You need at least 3 players."
            )

        # Create game
        game = Game(room=room, state=GameState.STARTING)

        # Initialize decks with all available cards
        await self.initialize_decks(game)

        # Hand out initial cards to all players
        await self.hand_out_initial_cards(game)

        # Set first leader (host)
        game.leader_index = 0
        room.players[0].is_host = True

        # Start first round
        await self.start_new_round(game)

        self.game_manager.active_games[room_id] = game
        return True

    # получаем все карты из базы данных и перемешиваем
    # сохраняем в переменные game.meme_deck и game.situation_deck
    async def initialize_decks(self, game: Game) -> None:
        """Initialize card decks with all available cards"""
        # This would typically load from database or static data
        # For now, creating sample cards

        meme_cards, situation_cards = await asyncio.gather(
            self.card_service.get_meme_cards(), self.card_service.get_situation_cards()
        )

        game.meme_deck = meme_cards
        game.situation_deck = situation_cards

        # Shuffle decks
        random.shuffle(game.meme_deck)
        random.shuffle(game.situation_deck)

    # из game.meme_deck в цикле раздаем по 1 карте каждому игроку 6 раз и сохраняем в player.handed_cards
    async def hand_out_initial_cards(self, game: Game) -> None:
        """Hand out 6 random meme cards to each player at game start"""
        for player in game.room.players:
            # Draw 6 unique cards
            for _ in range(self.settings.cards_per_player):  # cards_per_player = 6
                if game.meme_deck:
                    card = game.meme_deck.pop(0)
                    player.handed_cards.append(card)

    async def hand_out_one_card(self, game: Game):
        """Hand out one card to each player except the current leader"""
        current_leader = game.room.players[game.leader_index]

        for player in game.room.players:
            if player != current_leader and game.meme_deck:
                card = game.meme_deck.pop(0)
                player.handed_cards.append(card)

    async def get_situation_card(self, game: Game) -> Optional[SituationCard]:
        """Get a random situation card from available deck"""
        if not game.situation_deck:
            raise Exception("No situation cards available")

        # Filter out cards that are in cooldown
        available_cards = [
            card
            for card in game.situation_deck
            if card.used_round is None
            or (game.round_number - card.used_round)
            > self.settings.situation_card_cooldown
        ]

        if not available_cards:
            raise Exception("No situation cards available")

        return random.choice(available_cards)

    async def choose_leader(self, game: Game):
        """Choose next leader in connection order"""
        game.leader_index = (game.leader_index + 1) % len(game.room.players)
        return game.room.players[game.leader_index]

    async def start_new_round(self, game: Game):
        """Start a new round"""
        if game.state == GameState.WAITING:
            game.state = GameState.IN_PROGRESS

        game.round_number += 1
        current_leader = game.room.players[game.leader_index]

        # Get new situation card
        situation_card = await self.get_situation_card(game)
        if not situation_card:
            # No available situation cards, end game
            await self.end_game(game)
            return

        # Mark situation card as used
        situation_card.used_round = game.round_number

        # Create new round
        game.current_round = GameRound(
            round_number=game.round_number,
            leader=current_leader,
            situation_card=situation_card,
        )

        game.state = GameState.ROUND_ACTIVE

        # Hand out one card to each player except leader
        await self.hand_out_one_card(game)

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
        """End the current round and handle cleanup"""
        if not game.current_round:
            return

        round_data = game.current_round
        round_data.state = RoundState.ROUND_ENDED
        round_data.end_time = datetime.now()

        # Move used meme cards to discard pile
        for player_id, card in round_data.player_choices.items():
            card.round_to_return = game.round_number + game.settings.meme_card_cooldown
            game.meme_discard_pile.append(card)

            # Remove card from player's hand
            player = next((p for p in game.room.players if p.id == player_id), None)
            if player:
                player.handed_cards.remove(card)
                player.selected_card = None

        # Move used situation card to discard pile
        if round_data.situation_card:
            round_data.situation_card.round_to_return = (
                game.round_number + game.settings.situation_card_cooldown
            )
            game.situation_discard_pile.append(round_data.situation_card)

        # Check if game should end
        if await self.should_end_game(game):
            await self.end_game(game)
        else:
            # Choose next leader and start new round
            await self.choose_leader(game)
            await self.start_new_round(game)

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

        # Check if no more situation cards available
        available_situation_cards = [
            card
            for card in game.situation_deck
            if card.used_round is None
            or (game.round_number - card.used_round)
            > self.settings.situation_card_cooldown
        ]
        if not available_situation_cards:
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

    async def cleanup_room(self, room_id: str):
        """Clean up room and game data"""
        if room_id in self.game_manager.active_games:
            del self.game_manager.active_games[room_id]

        if room_id in self.game_manager.active_rooms:
            del self.game_manager.active_rooms[room_id]

        # Remove player connections for this room
        players_to_remove = [
            player_id
            for player_id, room in self.game_manager.player_connections.items()
            if room == room_id
        ]
        for player_id in players_to_remove:
            del self.game_manager.player_connections[player_id]

    async def get_available_meme_cards(self, game: Game) -> List[MemeCard]:
        """Get meme cards available for use (not in cooldown)"""
        return [
            card for card in game.meme_deck if card.round_to_return <= game.round_number
        ]

    async def get_available_situation_cards(self, game: Game) -> List[SituationCard]:
        """Get situation cards available for use (not in cooldown)"""
        return [
            card
            for card in game.situation_deck
            if card.round_to_return
            <= game.round_number(game.round_number - card.used_round)
            > self.settings.situation_card_cooldown
        ]

    def get_game_state(self, room_id: str) -> Optional[Game]:
        """Get current game state for a room"""
        return self.game_manager.active_games.get(room_id)

    def get_room_state(self, room_id: str) -> Optional[Room]:
        """Get current room state"""
        return self.game_manager.active_rooms.get(room_id)
