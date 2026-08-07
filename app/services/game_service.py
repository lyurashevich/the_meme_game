import asyncio
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
    PlayerNotFoundException,
    PlayerNotInRoomException,
    RoomHasNoOwnerException,
    RoundNotFoundException,
)
from app.game.connection_manager import ConnectionManager
from app.game.dataclasses import Game, GameRound, Player, Room
from app.game.enums import GameState, RoundState, WebsocketEvents
from app.game.game_manager import GameManager
from app.game.game_settings import GameSettings
from app.models import SituationCard
from app.schemas.game import GameScore, GameSettingsSchema
from app.schemas.room import LeaveRoomResponseSchema
from app.services.memes_services import CardService as MemeService
from app.services.room_service import RoomService
from app.services.situations_services import CardService as SituationService

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
        connection_manager: ConnectionManager,
    ):
        self.room_service = room_service
        self.game_manager = game_manager
        self.connection_manager = connection_manager

    async def get_game_settings(self, room_id: str) -> GameSettings:
        async with self.room_service.get_room_lock(room_id):
            return self.room_service.get_room(room_id).settings

    async def change_game_settings(self, room_id: str, player_id: str, data: GameSettingsSchema) -> GameSettings:
        async with self.room_service.get_room_lock(room_id):
            room = self.room_service.get_room(room_id)

            if room.owner_id != player_id:
                raise NotRoomOwnerException()

            room.settings = GameSettings(**data.model_dump())

            return room.settings

    async def finish_round_flow(self, room_id: str) -> None:
        async with self.room_service.get_room_lock(room_id):
            game = self.game_manager.get_game(room_id)
            await self._finalize_round(game)

            if self._should_end_game(game):
                messages = self._end_game_locked(
                    room_id,
                    message="Игра завершена: достигнут лимит раундов или необходимое количество очков для победы.",
                )
            else:
                await self._start_new_round(game)
                messages = self._round_started_messages_locked(game)

        await self._send_messages(messages)

    def _round_started_messages_locked(self, game: Game) -> list[tuple[list[str], dict]]:
        """Build the messages announcing that a new round has started.

        Assumes the room lock is held: reads the player list, current round and
        hands directly from ``game`` instead of re-fetching room state, so the
        returned messages reflect one consistent snapshot even though they are
        sent after the lock is released.
        """
        players = game.room.players
        players_ids = [player.id for player in players]
        current_round = self._validate_game_round_state(game)

        messages: list[tuple[list[str], dict]] = [
            (
                players_ids,
                {
                    "event": WebsocketEvents.ROUND_STATE_CHANGED.value,
                    "payload": {"state": RoundState.ROUND_ENDED.value},
                },
            )
        ]

        for player in players:
            messages.append(([player.id], self._build_round_started_payload(game, current_round, player)))

        messages.append(
            (
                players_ids,
                {
                    "event": WebsocketEvents.ROUND_STATE_CHANGED.value,
                    "payload": {"state": RoundState.CHOOSING_CARDS.value},
                },
            )
        )

        return messages

    @staticmethod
    def _change_round_state(current_round: GameRound, new_state: RoundState) -> bool:

        if current_round.state == new_state:
            return False

        current_round.state = new_state
        return True

    async def phase_timer(self, room_id: str, timeout: float):
        round_state_changed = False
        finish_round = False
        room = None

        await asyncio.sleep(timeout)

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

    @staticmethod
    def _validate_room_can_start_game(room: Room) -> None:
        if len(room.players) < MIN_PLAYERS:
            raise NotEnoughPlayersException()

    async def prepare_game(self, room_id: str, db: AsyncSession) -> Game | None:

        async with self.room_service.get_room_lock(room_id=room_id):
            room = self.room_service.get_room(room_id)
            self._validate_room_can_start_game(room)

            # Snapshot room.settings at game start: change_game_settings replaces
            # room.settings with a brand-new object rather than mutating it in
            # place, so this reference stays frozen at whatever it was when the
            # game started even if the owner changes room.settings mid-game.
            # game.settings (not room.settings) is therefore the authoritative
            # source for a running game - phase_timer's timeout included.
            game = Game(room=room, settings=room.settings)

            game.leader_index = 0
            self.game_manager.active_games[room_id] = game

            await self._initialize_decks(game, db)

        return game

    @staticmethod
    def _build_round_started_payload(game: Game, round_: GameRound | None, player: Player) -> dict:
        return {
            "event": WebsocketEvents.ROUND_STARTED.value,
            "payload": {
                "room_id": game.room.id,
                "leader_id": round_.leader_id if round_ and round_.leader else None,
                "current_round_number": round_.round_number if round_ else None,
                "current_situation_card": round_.situation_card.to_dict() if round_ else None,
                "score": {p.id: p.score for p in game.room.players},
                "players": [p.username for p in game.room.players],
                "player_cards": [card.to_dict() for card in player.handed_cards],
            },
        }

    @staticmethod
    def build_game_started_messages(game: Game) -> list[tuple[list[str], dict]]:
        players_ids = [player.id for player in game.room.players]
        messages: list[tuple[list[str], dict]] = [
            (players_ids, {"event": WebsocketEvents.GAME_STARTED.value, "payload": {"room_id": game.room.id}})
        ]

        for player in game.room.players:
            messages.append(([player.id], GameService._build_round_started_payload(game, game.current_round, player)))

        return messages

    async def start_first_round(self, room_id: str) -> Game:

        async with self.room_service.get_room_lock(room_id):
            game = self.game_manager.get_game(room_id)

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
                    player.handed_cards.append(card)

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

            self._validate_game_state(game, GameState.ACTIVE)
            current_round = self._validate_game_round_state(game, RoundState.CHOOSING_CARDS)

            player = next((player for player in game.room.players if player.id == player_id), None)
            if not player:
                raise PlayerNotFoundException()
            if player == current_round.leader:
                raise InvalidPlayerActionException(hint="Leader cannot choose a card")
            if player_id in current_round.player_choices:
                raise InvalidPlayerActionException(hint="Player already selected a card")

            selected_card = next((card for card in player.handed_cards if card.id == card_id), None)
            if not selected_card:
                raise CardNotFoundException()

            current_round.player_choices[player_id] = selected_card
            player.handed_cards.remove(selected_card)

            if self._validate_if_all_the_players_confirmed_their_choices(game):
                round_state_changed = self._change_round_state(current_round, RoundState.LEADER_CHOOSING)
                if round_state_changed:
                    self.game_manager.cancel_task(room_id, "phase_timer")

        if round_state_changed:
            await self.connection_manager.broadcast_to_players(
                [player.id for player in room.players],
                {
                    "event": WebsocketEvents.ROUND_STATE_CHANGED.value,
                    "payload": {"state": RoundState.LEADER_CHOOSING.value, "expected_cards": len(room.players) - 1},
                },
            )

        await self.connection_manager.broadcast_to_players(
            [player.id for player in room.players],
            {
                "event": WebsocketEvents.PLAYER_SELECTED_CARD.value,
                "card_id": selected_card.id,
                "image_url": selected_card.image_url,
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

            self._validate_game_state(game, GameState.ACTIVE)
            current_round = self._validate_game_round_state(game, RoundState.LEADER_CHOOSING)

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

        await self.connection_manager.broadcast_to_players(
            [player.id for player in self.room_service.get_room(room_id).players],
            {
                "event": WebsocketEvents.LEADER_HAS_CHOSEN_WINNER.value,
                "payload": {"winner_id": winner.id, "winner_username": winner.username, "card_id": card_id},
            },
        )

        await asyncio.sleep(self.WINNER_ANNOUNCEMENT_DELAY_SECONDS)

        try:
            await self.finish_round_flow(room_id)
        except (GameNotFoundException, InvalidRoundStateException, RoundNotFoundException):
            # The round was already finalized or aborted through another path while we were
            # waiting for the winner animation to play out (e.g. the leader disconnected
            # mid-animation and _handle_player_left_locked already started a new round).
            pass

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
        Acquires the room lock, runs the lock-free core and broadcasts the
        messages it returns (network I/O is kept out of the lock).
        """
        async with self.room_service.get_room_lock(room_id):
            room = self.room_service.get_room(room_id)

            if room.owner_id != player_id:
                raise NotRoomOwnerException()

            game = self.game_manager.get_game(room_id)
            if game.state == GameState.FINISHED:
                raise InvalidGameStateException(game_state="STARTING or ACTIVE")

            messages = self._end_game_locked(room_id, message="Игра завершена владельцем комнаты.")

        await self._send_messages(messages)

    def _end_game_locked(
        self,
        room_id: str,
        message: str = "Игра завершена: в комнате осталось меньше игроков, чем нужно для продолжения.",
    ) -> list[tuple[list[str], dict]]:
        """Finish the active game. Assumes the room lock is already held.

        Cancels timers, drops the game from the registry and resets the
        remaining players (cards + score) so a fresh game can be started.
        Mutates in-memory state only and RETURNS the outgoing messages
        ``(recipient_ids, payload)`` instead of sending them. Safe to call even
        if the room was already cleaned up (last player left).
        """
        self.game_manager.clear_room_tasks(room_id)

        game = self.game_manager.get_game(room_id)
        if game:
            game.state = GameState.FINISHED
            game.current_round = None

        room = self.room_service.get_room(room_id)
        if not room:
            return []

        final_scores = {player.id: player.score for player in room.players}
        for player in room.players:
            player.handed_cards.clear()
            player.score = 0
        players_ids = [player.id for player in room.players]

        if not players_ids:
            return []

        return [
            (
                players_ids,
                {
                    "event": WebsocketEvents.GAME_ENDED.value,
                    "payload": {
                        "room_id": room_id,
                        "message": message,
                        "final_scores": final_scores,
                    },
                },
            )
        ]

    @staticmethod
    def _deal_up_to_full_hand(game: Game, leader: Player) -> None:
        for player in game.room.players:
            if player.id == leader.id:
                continue
            while len(player.handed_cards) < CARDS_PER_PLAYER and game.meme_deck:
                player.handed_cards.append(game.meme_deck.pop(0))

    async def _handle_player_left_locked(self, room_id: str, leaver_id: str) -> list[tuple[list[str], dict]]:
        """Keep an active game consistent after a player leaves mid-game.

        Assumes the room lock is held and the leaver is already removed from
        ``room.players`` (and that at least ``MIN_PLAYERS`` players remain,
        otherwise the game is ended instead). Prunes the leaver's submitted
        choice, fixes leader rotation and, if the leaver was the current leader,
        aborts the round and starts a fresh one. Mutates state only and RETURNS
        the outgoing messages ``(recipient_ids, payload)`` in send order.
        """
        game = self.game_manager.get_game(room_id)
        if not game or not game.current_round:
            return []

        current_round = game.current_round
        players = game.room.players
        players_ids = [player.id for player in players]

        removed_card = current_round.player_choices.pop(leaver_id, None)

        messages: list[tuple[list[str], dict]] = []

        if current_round.leader.id != leaver_id:
            # Leader stays; keep the index pointing at the same player.
            game.leader_index = players.index(current_round.leader)

            # The leaver's card is still on everyone's table (it was broadcast when
            # they submitted it). Tell the clients to drop it so the leader can't
            # pick a card that no longer belongs to anyone in the round.
            if removed_card is not None:
                messages.append(
                    (
                        players_ids,
                        {
                            "event": WebsocketEvents.PLAYER_CARD_REMOVED.value,
                            "payload": {"card_id": removed_card.id},
                        },
                    )
                )

            if current_round.state == RoundState.CHOOSING_CARDS and (
                self._validate_if_all_the_players_confirmed_their_choices(game)
            ):
                if self._change_round_state(current_round, RoundState.LEADER_CHOOSING):
                    self.game_manager.cancel_task(room_id, "phase_timer")
                    messages.append(
                        (
                            players_ids,
                            {
                                "event": WebsocketEvents.ROUND_STATE_CHANGED.value,
                                "payload": {
                                    "state": RoundState.LEADER_CHOOSING.value,
                                    "expected_cards": len(players) - 1,
                                },
                            },
                        )
                    )
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
                return self._end_game_locked(room_id)
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

            messages.append(
                (
                    players_ids,
                    {
                        "event": WebsocketEvents.ROUND_STATE_CHANGED.value,
                        "payload": {"state": RoundState.ROUND_ENDED.value},
                    },
                )
            )
            for player in players:
                messages.append(([player.id], self._build_round_started_payload(game, new_round, player)))
            messages.append(
                (
                    players_ids,
                    {
                        "event": WebsocketEvents.ROUND_STATE_CHANGED.value,
                        "payload": {"state": RoundState.CHOOSING_CARDS.value},
                    },
                )
            )

        return messages

    async def _send_messages(self, messages: list[tuple[list[str], dict]]) -> None:
        """Broadcast a list of ``(recipient_ids, payload)`` messages in order."""
        for recipients, payload in messages:
            await self.connection_manager.broadcast_to_players(recipients, payload)

    async def process_leave(self, player: Player, room_id: str, confirm: bool) -> LeaveRoomResponseSchema:
        """Remove ``player`` from ``room_id`` atomically and keep the game consistent.

        The decision (is the game active? will too few players remain?) and the
        mutation happen under a single ``room_lock`` acquisition, so concurrent
        leaves cannot race into an inconsistent state. If leaving mid-game would
        drop the room below ``MIN_PLAYERS`` and ``confirm`` is not set, nothing is
        mutated and ``requires_confirmation=True`` is returned so the caller can
        ask the user to confirm. All network I/O happens after the lock releases.
        """
        messages: list[tuple[list[str], dict]] = []
        room_empty = False

        async with self.room_service.get_room_lock(room_id):
            room = self.room_service.get_room(room_id)  # raises RoomNotFoundException -> 404

            if player not in room.players:
                raise PlayerNotInRoomException()  # -> 409 instead of a raw 500 from remove_player

            try:
                game = self.game_manager.get_game(room_id)
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
            player.handed_cards.clear()
            self.game_manager.remove_player_connection(player.id)

            # If the owner just left and players remain, promote the next one
            # (join order) - otherwise room.owner_id keeps pointing at a player
            # who is no longer in the room, and nobody can pass the owner check
            # in change_game_settings/end_game ever again.
            new_owner_id = None
            if room.owner is player and room.players:
                room.reassign_owner()
                new_owner_id = room.owner_id

            if game_active and remaining_after < MIN_PLAYERS:
                messages.extend(self._end_game_locked(room_id))
            elif game_active:
                messages.extend(await self._handle_player_left_locked(room_id, player.id))

            room_empty = not room.players
            if not room_empty:
                messages.append(
                    (
                        [p.id for p in room.players],
                        {
                            "event": WebsocketEvents.PLAYER_LEFT_ROOM.value,
                            "payload": {
                                "player_id": player.id,
                                "player_username": player.username,
                                "room_id": room_id,
                                "new_owner_id": new_owner_id,
                            },
                        },
                    )
                )

        if room_empty:
            await self.room_service.cleanup_room(room_id)

        await self.connection_manager.send_personal_json(player.id, {"event": WebsocketEvents.YOU_LEFT_THE_ROOM.value})
        await self._send_messages(messages)

        return LeaveRoomResponseSchema(requires_confirmation=False)

    async def get_game_state(self, room_id: str) -> Optional[Game]:
        async with self.room_service.get_room_lock(room_id):
            game = self.game_manager.get_game(room_id)
        return game

    async def get_room_state(self, room_id: str) -> Optional[Room]:
        async with self.room_service.get_room_lock(room_id):
            room = self.room_service.get_room(room_id)
        return room

    async def get_current_round(self, room_id: str) -> GameRound:
        async with self.room_service.get_room_lock(room_id):
            game = self.game_manager.get_game(room_id)
            if not game.current_round:
                raise RoundNotFoundException()
            return game.current_round
