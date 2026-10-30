import asyncio
import logging
import random
from typing import Optional

from sqlalchemy.ext.asyncio import AsyncSession

from app.exceptions import (
    CardNotFoundException,
    GameNotFoundException,
    InvalidGameStateException,
    InvalidPlayerActionException,
    InvalidRoundStateException,
    NotEnoughCardsException,
    NotEnoughPlayersException,
    NotRoomOwnerException,
    NotRoundLeaderException,
    PlayerNotFoundException,
    PlayerNotInRoomException,
    RoomHasNoOwnerException,
    RoundNotFoundException,
)
from app.game.dataclasses import Game, GameRound, Player, Room
from app.game.enums import GameEndReason, GameState, RoundState, WebsocketEvents
from app.game.game_manager import GameManager
from app.game.game_settings import GameSettings
from app.models import SituationCard
from app.schemas.game import GameScore, GameSettingsSchema
from app.schemas.room import LeaveRoomResponseSchema
from app.services.memes_services import CardService as MemeService
from app.services.notifier import Notifier
from app.services.room_service import RoomService
from app.services.situations_services import CardService as SituationService
from app.services.snapshots import build_game_ended

logger = logging.getLogger(__name__)

MEME_CARDS_COOLDOWN = 20
SITUATION_CARDS_COOLDOWN = 30
CARDS_PER_PLAYER = 6
MIN_PLAYERS = 3


class GameService:
    # How long the winning card stays enlarged in the center of the screen before the
    # next round starts. Overridable per-instance (e.g. set to 0 in tests) since it's a
    # real asyncio.sleep and would otherwise add wall-clock time to every test that calls
    # leader_choose_winner.
    WINNER_ANNOUNCEMENT_DELAY_SECONDS = 2.5

    def __init__(
        self,
        room_service: RoomService,
        game_manager: GameManager,
        notifier: Notifier,
    ):
        self.room_service = room_service
        self.game_manager = game_manager
        self.notifier = notifier

    async def get_game_settings(self, room_id: str) -> GameSettings:
        async with self.room_service.get_room_lock(room_id):
            return (await self.room_service.get_room(room_id)).settings

    async def change_game_settings(self, room_id: str, player_id: str, data: GameSettingsSchema) -> GameSettings:
        async with self.room_service.get_room_lock(room_id):
            room = await self.room_service.get_room(room_id)

            if room.owner_id != player_id:
                raise NotRoomOwnerException()

            room.settings = GameSettings(**data.model_dump())

        await self.notifier.broadcast_room_state(room_id)

        return room.settings

    async def finish_round_flow(self, room_id: str) -> None:
        game_ended = None

        async with self.room_service.get_room_lock(room_id):
            game = await self.game_manager.get_game(room_id)
            await self._finalize_round(game)

            if self._should_end_game(game):
                game_ended = await self._end_game_locked(room_id, GameEndReason.LIMIT_REACHED)
            else:
                await self._start_new_round(game)

        await self._notify_room_changed(room_id, game_ended)

    async def _notify_room_changed(self, room_id: str, game_ended: dict | None = None) -> None:
        """Push the new state of the room to its players (after the room lock is released).

        ``game_ended`` is the payload returned by ``_end_game_locked``, if the change ended the game:
        players get the final results first, then the lobby snapshot, and the room list shows the
        room as waiting again.
        """
        if game_ended:
            await self.notifier.broadcast_event(room_id, WebsocketEvents.GAME_ENDED, game_ended)

        await self.notifier.broadcast_room_state(room_id)

        if game_ended:
            await self.notifier.broadcast_rooms_list()

    @staticmethod
    def _change_round_state(current_round: GameRound, new_state: RoundState) -> bool:

        if current_round.state == new_state:
            return False

        current_round.state = new_state
        return True

    async def phase_timer(self, room_id: str, timeout: float):
        round_state_changed = False
        finish_round = False

        await asyncio.sleep(timeout)

        async with self.room_service.get_room_lock(room_id):
            game = await self.game_manager.get_game(room_id)

            if not game or not game.current_round:
                return

            if game.current_round.state == RoundState.CHOOSING_CARDS:
                round_state_changed = self._change_round_state(game.current_round, RoundState.LEADER_CHOOSING)
            elif game.current_round.state == RoundState.LEADER_CHOOSING:
                finish_round = True

        if round_state_changed:
            await self.notifier.broadcast_room_state(room_id)

        if finish_round:
            await self.finish_round_flow(room_id)

    async def get_game_score(self, room_id: str) -> list[GameScore]:
        async with self.room_service.get_room_lock(room_id):
            game = await self.game_manager.get_game(room_id)

            return [
                GameScore(id=player.id, username=player.username, score=player.score) for player in game.room.players
            ]

    @staticmethod
    def _validate_room_can_start_game(room: Room) -> None:
        if len(room.players) < MIN_PLAYERS:
            raise NotEnoughPlayersException()

    async def start_game(self, room_id: str, player_id: str, db: AsyncSession) -> Game:
        """Owner-only entry point: prepare the game and start its first round."""
        async with self.room_service.get_room_lock(room_id):
            room = await self.room_service.get_room(room_id)
            if room.owner_id != player_id:
                raise NotRoomOwnerException()

        game = await self.prepare_game(room_id, db)
        await self.start_first_round(room_id)

        await self.notifier.broadcast_room_state(room_id)
        await self.notifier.broadcast_rooms_list()  # the room is no longer joinable

        return game

    async def prepare_game(self, room_id: str, db: AsyncSession) -> Game | None:

        async with self.room_service.get_room_lock(room_id=room_id):
            room = await self.room_service.get_room(room_id)
            self._validate_room_can_start_game(room)

            # Snapshot room.settings at game start: change_game_settings replaces
            # room.settings with a brand-new object rather than mutating it in
            # place, so this reference stays frozen at whatever it was when the
            # game started even if the owner changes room.settings mid-game.
            # game.settings (not room.settings) is therefore the authoritative
            # source for a running game - phase_timer's timeout included.
            game = Game(room=room, settings=room.settings)

            game.leader_index = 0
            await self.game_manager.add_game(room_id, game)

            await self._initialize_decks(game, db)

        return game

    async def start_first_round(self, room_id: str) -> Game:

        async with self.room_service.get_room_lock(room_id):
            game = await self.game_manager.get_game(room_id)

            self._validate_game_state(game, GameState.STARTING)

            owner = game.room.owner
            if owner is None:
                raise RoomHasNoOwnerException()

            situation_card = await self._get_situation_card(game)
            await self._hand_out_initial_cards(game)
            new_round = GameRound(
                round_number=1,
                leader=owner,
                situation_card=situation_card,
                game=game,  # state = RoundState.CHOOSING_CARDS
                time_limit=game.settings.round_time_limit,
            )
            game.current_round = new_round
            game.state = GameState.ACTIVE

            task = asyncio.create_task(self.phase_timer(room_id, timeout=game.settings.round_time_limit))

            self.game_manager.add_task(room_id, "phase_timer", task)

        return game

    async def _start_new_round(self, game: Game):
        prev_round = self._validate_game_round_state(game, RoundState.ROUND_ENDED)
        self._validate_game_state(game, GameState.ACTIVE)

        situation_card = await self._get_situation_card(game)
        await self._hand_out_one_card(game)

        round_number = prev_round.round_number + 1
        new_leader = await self._choose_leader(game)

        new_round = GameRound(
            round_number=round_number,
            leader=new_leader,
            situation_card=situation_card,
            game=game,  # state = RoundState.CHOOSING_CARDS
            time_limit=game.settings.round_time_limit,
        )
        game.current_round = new_round

        task = asyncio.create_task(self.phase_timer(game.room_id, timeout=game.settings.round_time_limit))

        self.game_manager.add_task(game.room_id, "phase_timer", task)

    @staticmethod
    def _validate_game_state(game: Game, state: GameState) -> None:
        if game.state != state:
            raise InvalidGameStateException(game_state=state.value)

    @staticmethod
    def _validate_game_round_state(game: Game, state: RoundState | None = None) -> GameRound:
        if game.current_round is None:
            raise RoundNotFoundException()

        if state and game.current_round.state != state:
            raise InvalidRoundStateException(round_state=state.value)

        return game.current_round

    @staticmethod
    async def _initialize_decks(game: Game, db: AsyncSession) -> None:
        game.meme_deck = list(await MemeService(db).get_meme_cards())
        game.situation_deck = list(await SituationService(db).get_situation_cards())

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
                    player.hand_cards.append(card)

    async def _hand_out_one_card(self, game: Game):

        self._validate_game_state(game, GameState.ACTIVE)
        self._validate_game_round_state(game, RoundState.ROUND_ENDED)

        current_leader = game.room.players[game.leader_index]

        if not game.meme_deck:
            raise NotEnoughCardsException()

        for player in game.room.players:
            if player == current_leader:
                continue
            card = game.meme_deck.pop(0)
            player.hand_cards.append(card)

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
        async with self.room_service.get_room_lock(room_id):
            game = await self.game_manager.get_game(room_id)

            self._validate_game_state(game, GameState.ACTIVE)
            current_round = self._validate_game_round_state(game, RoundState.CHOOSING_CARDS)

            player = next((player for player in game.room.players if player.id == player_id), None)
            if not player:
                raise PlayerNotFoundException()
            if player == current_round.leader:
                raise InvalidPlayerActionException(hint="Leader cannot choose a card")
            if player_id in current_round.player_choices:
                raise InvalidPlayerActionException(hint="Player already selected a card")

            selected_card = next((card for card in player.hand_cards if card.id == card_id), None)
            if not selected_card:
                raise CardNotFoundException()

            current_round.player_choices[player_id] = selected_card
            player.hand_cards.remove(selected_card)

            if self._validate_if_all_the_players_confirmed_their_choices(game):
                if self._change_round_state(current_round, RoundState.LEADER_CHOOSING):
                    self.game_manager.cancel_task(room_id, "phase_timer")

        await self.notifier.broadcast_room_state(room_id)

    @staticmethod
    def _validate_if_all_the_players_confirmed_their_choices(game: Game) -> bool:
        return (
            len(game.current_round.player_choices) == len(game.room.players) - 1
            if game and game.current_round
            else False
        )

    async def leader_choose_winner(self, room_id: str, player_id: str, card_id: int) -> None:
        """Record the winner and announce it; the next round starts in the background.

        Returns as soon as the winner is announced. The pause that keeps the winning card on
        screen and the transition to the next round (or the end of the game) run in the
        room's ``winner_announcement`` task.
        """
        async with self.room_service.get_room_lock(room_id):
            game = await self.game_manager.get_game(room_id)

            self._validate_game_state(game, GameState.ACTIVE)
            current_round = self._validate_game_round_state(game, RoundState.LEADER_CHOOSING)

            if current_round.leader.id != player_id:
                raise NotRoundLeaderException()

            winner_player_id = next(
                (player_id for player_id, card in current_round.player_choices.items() if card.id == card_id),
                None,
            )

            winner = next((p for p in game.room.players if p.id == winner_player_id), None)
            if not winner:
                raise PlayerNotFoundException()

            if winner == current_round.leader:
                raise InvalidPlayerActionException(hint="Leader cannot be a winner")

            if winner_player_id not in current_round.player_choices:
                raise InvalidPlayerActionException(hint="Winner must be selected from the players who submitted cards")

            current_round.winner = winner
            winner.score += 1

        # the moment itself (to play the animation), then the state with the updated score
        await self.notifier.broadcast_event(
            room_id, WebsocketEvents.ROUND_WINNER, {"winner_id": winner.id, "card_id": card_id}
        )
        await self.notifier.broadcast_room_state(room_id)

        task = asyncio.create_task(self._finish_round_after_announcement(room_id))
        self.game_manager.add_task(room_id, "winner_announcement", task)

    async def _finish_round_after_announcement(self, room_id: str) -> None:
        await asyncio.sleep(self.WINNER_ANNOUNCEMENT_DELAY_SECONDS)

        try:
            await self.finish_round_flow(room_id)
        except (GameNotFoundException, InvalidRoundStateException, RoundNotFoundException):
            # The round was already finalized or aborted through another path while we were
            # waiting for the winner animation to play out (e.g. the leader disconnected
            # mid-animation and _handle_player_left_locked already started a new round).
            pass
        except Exception:
            # nobody awaits this task, so the error would otherwise be lost
            logger.exception("Failed to finish the round in room %s", room_id)

    async def _finalize_round(self, game: Game):
        self._validate_game_state(game, GameState.ACTIVE)
        current_round = self._validate_game_round_state(game, RoundState.LEADER_CHOOSING)

        self._change_round_state(current_round, RoundState.ROUND_ENDED)
        for player_id, card in current_round.player_choices.items():  # {int: MemeCard}
            game.meme_discard_pile.setdefault(current_round.round_number, []).append(card)

        if current_round.situation_card:
            game.situation_discard_pile.setdefault(current_round.round_number, []).append(current_round.situation_card)

        current_round.finalized = True
        self.game_manager.cancel_task(game.room_id, "phase_timer")

        await self._process_meme_deck(game)
        await self._process_situation_deck(game)

    @staticmethod
    def _should_end_game(game: Game) -> bool:
        settings = game.settings

        if (
            settings.max_rounds is not None
            and game.current_round is not None
            and game.current_round.round_number >= settings.max_rounds
        ):
            return True

        if settings.score_to_win is not None:
            return any(player.score >= settings.score_to_win for player in game.room.players)

        return False

    async def end_game(self, room_id: str, player_id: str) -> None:
        """Finish the active game for a room and notify the remaining players.

        Only the room owner may end the game manually, and only while it
        hasn't already finished - STARTING and ACTIVE are both allowed, since
        the owner may want to cancel a game before its first round starts.
        Acquires the room lock, runs the lock-free core and notifies the
        players after releasing it (network I/O is kept out of the lock).
        """
        async with self.room_service.get_room_lock(room_id):
            room = await self.room_service.get_room(room_id)

            if room.owner_id != player_id:
                raise NotRoomOwnerException()

            game = await self.game_manager.get_game(room_id)
            if game.state == GameState.FINISHED:
                raise InvalidGameStateException(game_state="STARTING or ACTIVE")

            game_ended = await self._end_game_locked(room_id, GameEndReason.OWNER_ENDED)

        await self._notify_room_changed(room_id, game_ended)

    async def _end_game_locked(self, room_id: str, reason: GameEndReason) -> dict | None:
        """Finish the active game. Assumes the room lock is already held.

        Cancels timers, marks the game finished and resets the remaining players
        (cards + score) so a fresh game can be started. Mutates in-memory state
        only and RETURNS the ``game_ended`` payload (final scores are captured
        before the reset) instead of sending it, or ``None`` if nobody is left
        to tell.
        """
        self.game_manager.clear_room_tasks(room_id)

        game = await self.game_manager.get_game(room_id)
        if game:
            game.state = GameState.FINISHED
            game.current_round = None

        room = await self.room_service.get_room(room_id)

        final_scores = {player.id: player.score for player in room.players}
        for player in room.players:
            player.hand_cards.clear()
            player.score = 0

        if not room.players:
            return None

        return build_game_ended(room, reason.value, final_scores)

    @staticmethod
    def _deal_up_to_full_hand(game: Game, leader: Player) -> None:
        for player in game.room.players:
            if player.id == leader.id:
                continue
            while len(player.hand_cards) < CARDS_PER_PLAYER and game.meme_deck:
                player.hand_cards.append(game.meme_deck.pop(0))

    async def _handle_player_left_locked(self, room_id: str, leaver_id: str) -> dict | None:
        """Keep an active game consistent after a player leaves mid-game.

        Assumes the room lock is held and the leaver is already removed from
        ``room.players`` (and that at least ``MIN_PLAYERS`` players remain,
        otherwise the game is ended instead). Prunes the leaver's submitted
        choice, fixes leader rotation and, if the leaver was the current leader,
        aborts the round and starts a fresh one. Mutates state only; RETURNS the
        ``game_ended`` payload if the game had to end (no cards for a new round).
        """
        game = await self.game_manager.get_game(room_id)
        if not game or not game.current_round:
            return None

        current_round = game.current_round
        players = game.room.players

        # the leaver's card leaves the table (the next snapshot no longer shows it)
        current_round.player_choices.pop(leaver_id, None)

        if current_round.leader.id != leaver_id:
            # Leader stays; keep the index pointing at the same player.
            game.leader_index = players.index(current_round.leader)

            if current_round.state == RoundState.CHOOSING_CARDS and (
                self._validate_if_all_the_players_confirmed_their_choices(game)
            ):
                if self._change_round_state(current_round, RoundState.LEADER_CHOOSING):
                    self.game_manager.cancel_task(room_id, "phase_timer")
        else:
            # The leader left: abort the current round and start a new one.
            self.game_manager.cancel_task(room_id, "phase_timer")

            for card in current_round.player_choices.values():
                game.meme_discard_pile.setdefault(current_round.round_number, []).append(card)
            if current_round.situation_card:
                game.situation_discard_pile.setdefault(current_round.round_number, []).append(
                    current_round.situation_card
                )

            game.leader_index = game.leader_index % len(players)
            new_leader = players[game.leader_index]

            try:
                situation_card = await self._get_situation_card(game)
            except NotEnoughCardsException:
                # No situation card left to start a fresh round: end the game
                # gracefully instead of leaving the leave half-applied (500).
                return await self._end_game_locked(room_id, GameEndReason.OUT_OF_CARDS)
            self._deal_up_to_full_hand(game, new_leader)

            new_round = GameRound(
                round_number=current_round.round_number + 1,
                leader=new_leader,
                situation_card=situation_card,
                game=game,
                time_limit=game.settings.round_time_limit,
            )
            game.current_round = new_round

            task = asyncio.create_task(self.phase_timer(room_id, timeout=game.settings.round_time_limit))
            self.game_manager.add_task(room_id, "phase_timer", task)

        return None

    async def process_leave(self, player: Player, room_id: str, confirm: bool) -> LeaveRoomResponseSchema:
        """Remove ``player`` from ``room_id`` atomically and keep the game consistent.

        The decision (is the game active? will too few players remain?) and the
        mutation happen under a single ``room_lock`` acquisition, so concurrent
        leaves cannot race into an inconsistent state. If leaving mid-game would
        drop the room below ``MIN_PLAYERS`` and ``confirm`` is not set, nothing is
        mutated and ``requires_confirmation=True`` is returned so the caller can
        ask the user to confirm. All network I/O happens after the lock releases.
        """
        game_ended = None
        room_empty = False

        async with self.room_service.get_room_lock(room_id):
            room = await self.room_service.get_room(room_id)  # raises RoomNotFoundException -> 404

            if player not in room.players:
                raise PlayerNotInRoomException()  # -> 409 instead of a raw 500 from remove_player

            try:
                game = await self.game_manager.get_game(room_id)
            except GameNotFoundException:
                game = None

            game_active = bool(game) and game.state == GameState.ACTIVE if game and game.current_round else None
            remaining_after = len(room.players) - 1

            # Leaving mid-game would drop the room below the minimum: ask the
            # leaver to confirm before ending the game for everyone.
            if game_active and remaining_after < MIN_PLAYERS and not confirm:
                return LeaveRoomResponseSchema(requires_confirmation=True)

            room.remove_player(player)
            player.room_id = None
            player.hand_cards.clear()

            # If the owner just left and players remain, promote the next one
            # (join order) - otherwise room.owner_id keeps pointing at a player
            # who is no longer in the room, and nobody can pass the owner check
            # in change_game_settings/end_game ever again.
            if room.owner is player and room.players:
                room.reassign_owner()

            if game_active and remaining_after < MIN_PLAYERS:
                game_ended = await self._end_game_locked(room_id, GameEndReason.NOT_ENOUGH_PLAYERS)
            elif game_active:
                game_ended = await self._handle_player_left_locked(room_id, player.id)

            room_empty = not room.players

        if room_empty:
            await self.room_service.cleanup_room(room_id)

        await self.notifier.send_event(player.id, WebsocketEvents.YOU_LEFT_ROOM, {"room_id": room_id})
        await self._notify_room_changed(room_id, game_ended)  # no-op for an emptied room
        if not game_ended:
            await self.notifier.broadcast_rooms_list()  # players count changed (and the leaver is back in the lobby)

        return LeaveRoomResponseSchema(requires_confirmation=False)

    async def get_game_state(self, room_id: str) -> Optional[Game]:
        async with self.room_service.get_room_lock(room_id):
            game = await self.game_manager.get_game(room_id)
        return game

    async def get_room_state(self, room_id: str) -> Optional[Room]:
        async with self.room_service.get_room_lock(room_id):
            room = await self.room_service.get_room(room_id)
        return room

    async def get_current_round(self, room_id: str) -> GameRound:
        async with self.room_service.get_room_lock(room_id):
            game = await self.game_manager.get_game(room_id)
            if not game.current_round:
                raise RoundNotFoundException()
            return game.current_round
