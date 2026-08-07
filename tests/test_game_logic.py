import asyncio
from unittest.mock import AsyncMock, patch

import pytest

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
    RoomHasNoOwnerException,
    RoomNotFoundException,
    RoundNotFoundException,
)
from app.game.enums import GameState, RoundState, WebsocketEvents
from app.models import MemeCard
from app.schemas.game import GameSettingsSchema
from app.services.game_service import CARDS_PER_PLAYER


async def _play_round_to_completion(game_service, game):
    """Test helper: every non-leader player picks a card, the leader picks a winner.

    Drives ``player_select_card`` + ``leader_choose_winner`` for the game's
    current round, mirroring the sequence already inlined in several tests
    below. Only pulled into a helper here because the deck-exhaustion test
    needs to repeat it several times in a loop.
    """
    current_round = game.current_round
    for player in game.room.players:
        if player is not current_round.leader:
            await game_service.player_select_card(game.room_id, player.id, player.handed_cards[0].id)

    winner = next(player for player in game.room.players if player is not current_round.leader)
    winner_card_id = current_round.player_choices[winner.id].id
    current_round.state = RoundState.LEADER_CHOOSING

    await game_service.leader_choose_winner(game.room_id, winner_card_id)
    return winner


class TestGameLogic:
    async def test_get_room(self, test_room, room_service):
        room = room_service.get_room(test_room.id)

        assert room
        assert room.id == test_room.id

    async def test_get_room__not_found(self, room_service):
        with pytest.raises(RoomNotFoundException) as e:
            room_service.get_room("qwerty")

        assert str(e.value.message) == "Room not found"

    async def test_prepare_game(
        self, test_room_with_players, mock_situation_cards, mock_meme_cards, game_service, game_manager, db_session
    ):

        with patch("app.services.game_service.MemeService.get_meme_cards", return_value=mock_meme_cards), patch(
            "app.services.game_service.SituationService.get_situation_cards", return_value=mock_situation_cards
        ):

            game = await game_service.prepare_game(test_room_with_players.id, db=db_session)

        assert not game.current_round
        assert game.meme_deck_count == len(mock_meme_cards)
        assert game.situation_deck_count == len(mock_situation_cards)
        assert not game.meme_discard_pile
        assert not game.situation_discard_pile
        assert game.state == GameState.STARTING
        assert game.room == test_room_with_players
        assert game_manager.active_games[test_room_with_players.id] == game

    async def test_prepare_game__not_enough_players(self, test_room, game_service, db_session):
        with pytest.raises(NotEnoughPlayersException) as e:
            await game_service.prepare_game(test_room.id, db=db_session)

        assert str(e.value.message) == NotEnoughPlayersException.message

    async def test_prepare_game__room_not_found(self, game_service, db_session):
        with pytest.raises(RoomNotFoundException) as e:
            await game_service.prepare_game("qwerty", db=db_session)

        assert str(e.value.message) == RoomNotFoundException.message

    async def test_build_game_started_messages(self, prepared_game, game_service):
        messages = game_service.build_game_started_messages(prepared_game)

        assert len(messages) == 1 + len(prepared_game.room.players)

        game_started_recipients, game_started_payload = messages[0]
        assert game_started_recipients == [player.id for player in prepared_game.room.players]
        assert game_started_payload == {
            "event": WebsocketEvents.GAME_STARTED.value,
            "payload": {"room_id": prepared_game.room.id},
        }

        for (recipients, payload), player in zip(messages[1:], prepared_game.room.players):
            assert recipients == [player.id]
            assert payload["event"] == WebsocketEvents.ROUND_STARTED.value
            assert payload["payload"]["room_id"] == prepared_game.room.id
            assert payload["payload"]["leader_id"] is None
            assert payload["payload"]["player_cards"] == [card.to_dict() for card in player.handed_cards]

    async def test_start_first_round(self, prepared_game, game_service):
        await game_service.start_first_round(prepared_game.room_id)

        assert prepared_game.current_round.round_number == 1
        assert prepared_game.current_round.situation_card not in prepared_game.situation_deck
        assert not prepared_game.current_round.winner
        assert prepared_game.leader_index == 0
        assert prepared_game.state == GameState.ACTIVE
        assert prepared_game.current_round.state == RoundState.CHOOSING_CARDS
        for player in prepared_game.room.players:
            assert len(player.handed_cards) == CARDS_PER_PLAYER

    async def test_start_first_round__wrong_game_state(self, prepared_game, game_service):
        prepared_game.state = GameState.FINISHED
        with pytest.raises(InvalidGameStateException) as e:
            await game_service.start_first_round(prepared_game.room_id)

        assert (
            str(e.value.message)
            == f"Invalid game state. Game state must be {GameState.STARTING.value} to perform this action"
        )  # todo: подправить

    async def test_start_first_round__room_has_no_owner(self, prepared_game, game_service):
        prepared_game.room.owner = None

        with pytest.raises(RoomHasNoOwnerException) as e:
            await game_service.start_first_round(prepared_game.room_id)

        assert str(e.value.message) == RoomHasNoOwnerException.message

    async def test_start_first_round__no_situation_cards(self, prepared_game, game_service):
        prepared_game.situation_deck.clear()
        with pytest.raises(NotEnoughCardsException) as e:
            await game_service.start_first_round(prepared_game.room_id)

        assert str(e.value.message) == NotEnoughCardsException.message

    async def test_start_first_round__no_meme_cards(self, prepared_game, game_service):
        prepared_game.meme_deck.clear()
        with pytest.raises(NotEnoughCardsException) as e:
            await game_service.start_first_round(prepared_game.room_id)

        assert str(e.value.message) == NotEnoughCardsException.message

    async def test_player_select_card(self, prepared_game, game_service):
        await game_service.start_first_round(prepared_game.room_id)
        player = prepared_game.room.players[1]
        selected_card = player.handed_cards[0]

        await game_service.player_select_card(prepared_game.room_id, player.id, selected_card.id)

        assert prepared_game.current_round.player_choices[player.id] == selected_card
        assert selected_card not in player.handed_cards
        assert len(player.handed_cards) == CARDS_PER_PLAYER - 1

    async def test_player_select_card__player_is_leader(self, prepared_game, game_service):
        await game_service.start_first_round(prepared_game.room_id)
        player = prepared_game.room.players[0]
        selected_card = player.handed_cards[0]

        with pytest.raises(InvalidPlayerActionException) as e:
            await game_service.player_select_card(prepared_game.room_id, player.id, selected_card.id)

        assert str(e.value.message) == "Invalid player action. Leader cannot choose a card"  # todo: подправить

    async def test_player_select_card__player_not_found(self, prepared_game, game_service):
        await game_service.start_first_round(prepared_game.room_id)

        with pytest.raises(PlayerNotFoundException) as e:
            await game_service.player_select_card(prepared_game.room_id, "player.id", 999)

        assert str(e.value.message) == PlayerNotFoundException.message

    async def test_player_select_card__card_not_found(self, prepared_game, game_service):
        await game_service.start_first_round(prepared_game.room_id)
        player = prepared_game.room.players[1]

        with pytest.raises(CardNotFoundException) as e:
            await game_service.player_select_card(prepared_game.room_id, player.id, 999)

        assert str(e.value.message) == CardNotFoundException.message

    async def test_player_select_card__wrong_state(self, prepared_game, game_service):
        await game_service.start_first_round(prepared_game.room_id)
        prepared_game.state = GameState.FINISHED
        player = prepared_game.room.players[1]
        selected_card = player.handed_cards[0]

        with pytest.raises(InvalidGameStateException) as e:
            await game_service.player_select_card(prepared_game.room_id, player.id, selected_card.id)

        assert (
            str(e.value.message)
            == f"Invalid game state. Game state must be {GameState.ACTIVE.value} to perform this action"
        )  # todo: подправить

    async def test_player_select_card__card_already_selected(self, prepared_game, game_service):
        await game_service.start_first_round(prepared_game.room_id)
        player = prepared_game.room.players[1]
        prepared_game.current_round.player_choices[player.id] = player.handed_cards[0]
        selected_card = player.handed_cards[1]

        with pytest.raises(InvalidPlayerActionException) as e:
            await game_service.player_select_card(prepared_game.room_id, player.id, selected_card.id)

        assert str(e.value.message) == "Invalid player action. Player already selected a card"  # todo: подправить

    async def test_player_select_card__round_not_found(self, prepared_game, game_service):
        await game_service.start_first_round(prepared_game.room_id)
        prepared_game.current_round = None
        player = prepared_game.room.players[1]
        selected_card = player.handed_cards[0]

        with pytest.raises(RoundNotFoundException) as e:
            await game_service.player_select_card(prepared_game.room_id, player.id, selected_card.id)

        assert str(e.value.message) == RoundNotFoundException.message

    async def test_player_select_card__wrong_round_state(self, prepared_game, game_service):
        await game_service.start_first_round(prepared_game.room_id)
        player = prepared_game.room.players[1]
        selected_card = player.handed_cards[0]
        prepared_game.current_round.state = RoundState.LEADER_CHOOSING

        with pytest.raises(InvalidRoundStateException) as e:
            await game_service.player_select_card(prepared_game.room_id, player.id, selected_card.id)

        assert (
            str(e.value.message)
            == f"Invalid round state. Round state must be {RoundState.CHOOSING_CARDS.value} to perform this action"
        )  # todo: подправить

    async def test_leader_choose_winner(self, prepared_game, game_service):
        await game_service.start_first_round(prepared_game.room_id)
        for player in prepared_game.room.players:
            if player is not prepared_game.current_round.leader:
                await game_service.player_select_card(prepared_game.room_id, player.id, player.handed_cards[0].id)

        game_service.WINNER_ANNOUNCEMENT_DELAY_SECONDS = 0

        winner = prepared_game.room.players[2]
        winner_card_id = prepared_game.current_round.player_choices[winner.id].id
        prepared_game.current_round.state = RoundState.LEADER_CHOOSING

        await game_service.leader_choose_winner(prepared_game.room_id, winner_card_id)

        assert winner.score == 1

    async def test_leader_choose_winner__game_not_found(self, prepared_game, test_game, game_service):

        winner = prepared_game.room.players[2]

        with pytest.raises(GameNotFoundException) as e:
            await game_service.leader_choose_winner(test_game.room_id, winner.id)

        assert str(e.value.message) == GameNotFoundException.message

    async def test_leader_choose_winner__round_not_found(self, prepared_game, game_service):
        await game_service.start_first_round(prepared_game.room_id)
        prepared_game.current_round = None

        winner = prepared_game.room.players[2]

        with pytest.raises(RoundNotFoundException) as e:
            await game_service.leader_choose_winner(prepared_game.room_id, winner.id)

        assert str(e.value.message) == RoundNotFoundException.message

    async def test_leader_choose_winner__wrong_round_state(self, prepared_game, game_service):
        await game_service.start_first_round(prepared_game.room_id)
        for player in prepared_game.room.players:
            if player is not prepared_game.current_round.leader:
                await game_service.player_select_card(prepared_game.room_id, player.id, player.handed_cards[0].id)

        winner_id = prepared_game.room.players[2].id
        prepared_game.current_round.state = RoundState.ROUND_ENDED

        with pytest.raises(InvalidRoundStateException) as e:
            await game_service.leader_choose_winner(
                prepared_game.room_id, prepared_game.current_round.player_choices[winner_id].id
            )

        assert (
            str(e.value)
            == f"Invalid round state. Round state must be {RoundState.LEADER_CHOOSING.value} to perform this action"
        )  # todo: подправить

    async def test_leader_choose_winner__wrong_game_state(self, prepared_game, game_service):
        await game_service.start_first_round(prepared_game.room_id)
        prepared_game.state = GameState.FINISHED

        winner = prepared_game.room.players[2]

        with pytest.raises(InvalidGameStateException) as e:
            await game_service.leader_choose_winner(prepared_game.room_id, winner.id)

        assert (
            str(e.value.message)
            == f"Invalid game state. Game state must be {GameState.ACTIVE.value} to perform this action"
        )  # todo: подправить

    async def test_leader_choose_winner__player_not_found(self, prepared_game, game_service):
        await game_service.start_first_round(prepared_game.room_id)
        prepared_game.current_round.state = RoundState.LEADER_CHOOSING

        with pytest.raises(PlayerNotFoundException) as e:
            await game_service.leader_choose_winner(prepared_game.room_id, "winner.id")

        assert str(e.value.message) == PlayerNotFoundException.message

    async def test_leader_choose_winner__announces_winner_before_next_round_starts(self, prepared_game, game_service):
        """``leader_has_chosen_winner`` must reach clients before the table is cleared and
        the next round's data is sent, otherwise the winning card is already gone from the
        client's DOM by the time it learns which card won (see the frontend animation)."""
        await game_service.start_first_round(prepared_game.room_id)
        for player in prepared_game.room.players:
            if player is not prepared_game.current_round.leader:
                await game_service.player_select_card(prepared_game.room_id, player.id, player.handed_cards[0].id)

        winner = prepared_game.room.players[2]
        winner_card_id = prepared_game.current_round.player_choices[winner.id].id
        prepared_game.current_round.state = RoundState.LEADER_CHOOSING

        game_service.WINNER_ANNOUNCEMENT_DELAY_SECONDS = 0

        sent_messages = []

        async def record_broadcast(player_ids, message):
            sent_messages.append(message)

        async def record_personal(player_id, message):
            sent_messages.append(message)

        game_service.connection_manager.broadcast_to_players = AsyncMock(side_effect=record_broadcast)
        game_service.connection_manager.send_personal_json = AsyncMock(side_effect=record_personal)

        await game_service.leader_choose_winner(prepared_game.room_id, winner_card_id)

        events_in_order = [message["event"] for message in sent_messages]
        winner_event_index = events_in_order.index(WebsocketEvents.LEADER_HAS_CHOSEN_WINNER.value)
        round_started_index = events_in_order.index(WebsocketEvents.ROUND_STARTED.value)

        assert winner_event_index < round_started_index
        assert events_in_order.count(WebsocketEvents.LEADER_HAS_CHOSEN_WINNER.value) == 1

        winner_message = sent_messages[winner_event_index]
        assert winner_message["payload"] == {
            "winner_id": winner.id,
            "winner_username": winner.username,
            "card_id": winner_card_id,
        }

    async def test_leader_choose_winner__leader_leaving_during_delay_is_a_no_op(self, prepared_game, game_service):
        """While the winning card is on display, the leader may disconnect before the
        delayed ``finish_round_flow`` runs. ``_handle_player_left_locked`` already aborts
        the round and starts a fresh one in that case, so the delayed continuation must
        not blow up (or double-advance the round) when it finally wakes up and finds the
        round it was waiting on no longer exists."""
        await game_service.start_first_round(prepared_game.room_id)
        for player in prepared_game.room.players:
            if player is not prepared_game.current_round.leader:
                await game_service.player_select_card(prepared_game.room_id, player.id, player.handed_cards[0].id)

        leader = prepared_game.current_round.leader
        winner = prepared_game.room.players[2]
        winner_card_id = prepared_game.current_round.player_choices[winner.id].id
        prepared_game.current_round.state = RoundState.LEADER_CHOOSING

        resume_after_animation = asyncio.Event()
        real_sleep = asyncio.sleep  # patching "asyncio.sleep" below replaces this name process-wide

        async def fake_sleep(seconds):
            if seconds == game_service.WINNER_ANNOUNCEMENT_DELAY_SECONDS:
                await resume_after_animation.wait()
            else:
                # Must still actually suspend for any other duration (including the
                # `asyncio.sleep(0)` below) - otherwise nothing ever yields control back
                # to the event loop before `process_leave` runs, and the task we just
                # created never gets a chance to start.
                await real_sleep(seconds)

        with patch("app.services.game_service.asyncio.sleep", side_effect=fake_sleep):
            task = asyncio.create_task(game_service.leader_choose_winner(prepared_game.room_id, winner_card_id))
            await asyncio.sleep(0)  # let leader_choose_winner run up to (and start) its delay

            await game_service.process_leave(leader, prepared_game.room_id, confirm=True)

            resume_after_animation.set()
            await task  # must not raise, even though the round was replaced while waiting

        assert prepared_game.current_round is not None
        assert prepared_game.current_round.round_number == 2
        assert prepared_game.current_round.winner is None
        assert prepared_game.current_round.leader is not leader

        game_service.game_manager.clear_room_tasks(prepared_game.room_id)

    async def test_end_round(self, prepared_game, game_service):
        await game_service.start_first_round(prepared_game.room_id)
        for player in prepared_game.room.players:
            if player is not prepared_game.current_round.leader:
                await game_service.player_select_card(prepared_game.room_id, player.id, player.handed_cards[0].id)

        game_service.WINNER_ANNOUNCEMENT_DELAY_SECONDS = 0

        winner = prepared_game.room.players[2]
        prepared_game.current_round.state = RoundState.LEADER_CHOOSING

        await game_service.leader_choose_winner(
            prepared_game.room_id, prepared_game.current_round.player_choices[winner.id].id
        )

        assert len(prepared_game.meme_discard_pile) > 0
        assert len(prepared_game.situation_discard_pile) > 0

    async def test_end_round__round_not_found(self, prepared_game, game_service):
        prepared_game.state = GameState.ACTIVE
        with pytest.raises(RoundNotFoundException) as e:
            await game_service._finalize_round(prepared_game)

        assert str(e.value.message) == RoundNotFoundException.message

    async def test_end_round__game_not_active(self, prepared_game, game_service):
        prepared_game.state = GameState.FINISHED
        with pytest.raises(InvalidGameStateException) as e:
            await game_service._finalize_round(prepared_game)

        assert (
            str(e.value.message)
            == f"Invalid game state. Game state must be {GameState.ACTIVE.value} to perform this action"
        )  # todo: подправить

    async def test_start_new_round(self, prepared_game, game_service):
        await game_service.start_first_round(prepared_game.room_id)
        for player in prepared_game.room.players:
            if player is not prepared_game.current_round.leader:
                await game_service.player_select_card(prepared_game.room_id, player.id, player.handed_cards[0].id)

        game_service.WINNER_ANNOUNCEMENT_DELAY_SECONDS = 0

        prepared_game.current_round.state = RoundState.LEADER_CHOOSING

        await game_service.leader_choose_winner(
            prepared_game.room_id, prepared_game.current_round.player_choices[prepared_game.room.players[2].id].id
        )

        assert prepared_game.current_round.round_number == 2
        assert prepared_game.leader_index == 1
        assert not prepared_game.current_round.winner
        assert prepared_game.state == GameState.ACTIVE
        assert prepared_game.current_round.state == RoundState.CHOOSING_CARDS
        assert len(prepared_game.meme_discard_pile) > 0
        assert len(prepared_game.meme_discard_pile) > 0
        assert prepared_game.current_round.situation_card not in prepared_game.situation_deck
        assert prepared_game.current_round.situation_card not in prepared_game.situation_discard_pile
        for player in prepared_game.room.players:
            assert len(player.handed_cards) == CARDS_PER_PLAYER
            assert len(set(player.handed_cards)) == CARDS_PER_PLAYER

    async def test_should_end_game__max_rounds_reached(self, prepared_game, game_service):
        await game_service.start_first_round(prepared_game.room_id)
        prepared_game.settings.max_rounds = 3
        prepared_game.current_round.round_number = 3

        assert game_service._should_end_game(prepared_game) is True

    async def test_should_end_game__max_rounds_not_reached(self, prepared_game, game_service):
        await game_service.start_first_round(prepared_game.room_id)
        prepared_game.settings.max_rounds = 3
        prepared_game.current_round.round_number = 2

        assert game_service._should_end_game(prepared_game) is False

    async def test_should_end_game__score_to_win_reached(self, prepared_game, game_service):
        await game_service.start_first_round(prepared_game.room_id)
        prepared_game.settings.score_to_win = 2
        prepared_game.room.players[1].score = 2

        assert game_service._should_end_game(prepared_game) is True

    async def test_should_end_game__score_to_win_not_reached(self, prepared_game, game_service):
        await game_service.start_first_round(prepared_game.room_id)
        prepared_game.settings.score_to_win = 2
        for player in prepared_game.room.players:
            player.score = 1

        assert game_service._should_end_game(prepared_game) is False

    async def test_should_end_game__unlimited_settings_never_end(self, prepared_game, game_service):
        await game_service.start_first_round(prepared_game.room_id)
        prepared_game.settings.max_rounds = None
        prepared_game.settings.score_to_win = None
        prepared_game.current_round.round_number = 100
        for player in prepared_game.room.players:
            player.score = 100

        assert game_service._should_end_game(prepared_game) is False

    async def test_should_end_game__uses_game_settings_not_room_settings(self, prepared_game, game_service):
        await game_service.start_first_round(prepared_game.room_id)
        prepared_game.settings.score_to_win = None
        prepared_game.room.players[1].score = 1

        # change_game_settings replaces room.settings with a new object; game.settings
        # (the snapshot captured once at game start) must stay untouched.
        await game_service.change_game_settings(
            room_id=prepared_game.room_id,
            player_id=prepared_game.room.owner_id,
            data=GameSettingsSchema(round_time_limit=60, score_to_win=1),
        )

        assert game_service._should_end_game(prepared_game) is False

    async def test_leader_choose_winner__ends_game_on_score_to_win(self, prepared_game, game_service):
        prepared_game.settings.score_to_win = 1
        await game_service.start_first_round(prepared_game.room_id)

        for player in prepared_game.room.players:
            if player is not prepared_game.current_round.leader:
                await game_service.player_select_card(prepared_game.room_id, player.id, player.handed_cards[0].id)

        game_service.WINNER_ANNOUNCEMENT_DELAY_SECONDS = 0

        winner = prepared_game.room.players[2]
        winner_card_id = prepared_game.current_round.player_choices[winner.id].id
        prepared_game.current_round.state = RoundState.LEADER_CHOOSING

        await game_service.leader_choose_winner(prepared_game.room_id, winner_card_id)

        assert prepared_game.state == GameState.FINISHED
        assert prepared_game.current_round is None
        for player in prepared_game.room.players:
            assert player.score == 0
            assert player.handed_cards == []

    async def test_leader_choose_winner__ends_game_on_max_rounds(self, prepared_game, game_service):
        prepared_game.settings.max_rounds = 1
        await game_service.start_first_round(prepared_game.room_id)

        for player in prepared_game.room.players:
            if player is not prepared_game.current_round.leader:
                await game_service.player_select_card(prepared_game.room_id, player.id, player.handed_cards[0].id)

        game_service.WINNER_ANNOUNCEMENT_DELAY_SECONDS = 0

        winner = prepared_game.room.players[2]
        winner_card_id = prepared_game.current_round.player_choices[winner.id].id
        prepared_game.current_round.state = RoundState.LEADER_CHOOSING

        await game_service.leader_choose_winner(prepared_game.room_id, winner_card_id)

        assert prepared_game.state == GameState.FINISHED
        assert prepared_game.current_round is None

    async def test_leader_choose_winner__game_ended_sends_game_ended_event(self, prepared_game, game_service):
        prepared_game.settings.score_to_win = 1
        await game_service.start_first_round(prepared_game.room_id)

        for player in prepared_game.room.players:
            if player is not prepared_game.current_round.leader:
                await game_service.player_select_card(prepared_game.room_id, player.id, player.handed_cards[0].id)

        game_service.WINNER_ANNOUNCEMENT_DELAY_SECONDS = 0

        winner = prepared_game.room.players[2]
        winner_card_id = prepared_game.current_round.player_choices[winner.id].id
        prepared_game.current_round.state = RoundState.LEADER_CHOOSING

        game_service.connection_manager.broadcast_to_players = AsyncMock()
        game_service.connection_manager.send_personal_json = AsyncMock()

        await game_service.leader_choose_winner(prepared_game.room_id, winner_card_id)

        sent_events = [
            call.args[1]["event"] for call in game_service.connection_manager.broadcast_to_players.await_args_list
        ]
        assert WebsocketEvents.GAME_ENDED.value in sent_events
        game_service.connection_manager.send_personal_json.assert_not_awaited()

    async def test_leader_choose_winner__max_rounds_ends_before_deck_exhaustion(self, prepared_game, game_service):
        # Top up the meme deck so this test only exercises the situation-card deck
        # (5 cards, matching max_rounds below) — the meme deck's own cooldown/
        # recycling mechanics are unrelated to the behavior under test.
        prepared_game.meme_deck.extend(
            MemeCard(id=1000 + i, image_url=f"http://memes.org/extra/{i}") for i in range(50)
        )

        game_service.WINNER_ANNOUNCEMENT_DELAY_SECONDS = 0

        prepared_game.settings.max_rounds = 5
        await game_service.start_first_round(prepared_game.room_id)

        for _ in range(4):
            await _play_round_to_completion(game_service, prepared_game)

        assert prepared_game.current_round.round_number == 5
        assert prepared_game.situation_deck_count == 0

        await _play_round_to_completion(game_service, prepared_game)

        assert prepared_game.state == GameState.FINISHED
        assert prepared_game.current_round is None

    async def test_end_game_locked__default_message_preserved(self, prepared_game, game_service):
        messages = game_service._end_game_locked(prepared_game.room_id)

        assert len(messages) == 1
        _, payload = messages[0]
        assert (
            payload["payload"]["message"]
            == "Игра завершена: в комнате осталось меньше игроков, чем нужно для продолжения."
        )

    async def test_end_game_locked__custom_message(self, prepared_game, game_service):
        messages = game_service._end_game_locked(prepared_game.room_id, message="custom message")

        assert len(messages) == 1
        _, payload = messages[0]
        assert payload["payload"]["message"] == "custom message"

    async def test_end_game_locked__includes_final_scores_before_reset(self, prepared_game, game_service):
        prepared_game.room.players[0].score = 3
        prepared_game.room.players[1].score = 1

        messages = game_service._end_game_locked(prepared_game.room_id)

        _, payload = messages[0]
        assert payload["payload"]["final_scores"] == {
            prepared_game.room.players[0].id: 3,
            prepared_game.room.players[1].id: 1,
            prepared_game.room.players[2].id: 0,
            prepared_game.room.players[3].id: 0,
        }
        for player in prepared_game.room.players:
            assert player.score == 0

    async def test_end_game__owner_ends_game(self, prepared_game, game_service):
        owner_id = prepared_game.room.owner_id

        await game_service.end_game(prepared_game.room_id, owner_id)

        assert prepared_game.state == GameState.FINISHED
        assert prepared_game.current_round is None
        for player in prepared_game.room.players:
            assert player.score == 0
            assert player.handed_cards == []

    async def test_end_game__not_owner_raises(self, prepared_game, game_service):
        with pytest.raises(NotRoomOwnerException) as e:
            await game_service.end_game(prepared_game.room_id, "not-the-owner")

        assert str(e.value.message) == NotRoomOwnerException.message
        assert prepared_game.state == GameState.STARTING

    async def test_end_game__no_active_game_raises(self, test_room_with_players, game_service):
        with pytest.raises(GameNotFoundException) as e:
            await game_service.end_game(test_room_with_players.id, test_room_with_players.owner_id)

        assert str(e.value.message) == GameNotFoundException.message

    async def test_end_game__already_finished_raises(self, prepared_game, game_service):
        prepared_game.state = GameState.FINISHED

        with pytest.raises(InvalidGameStateException) as e:
            await game_service.end_game(prepared_game.room_id, prepared_game.room.owner_id)

        assert (
            str(e.value.message) == "Invalid game state. Game state must be STARTING or ACTIVE to perform this action"
        )

    async def test_process_leave__owner_leaving_lobby_reassigns_ownership(self, test_room_with_players, game_service):
        owner = test_room_with_players.owner
        next_owner = test_room_with_players.players[1]  # join order: owner, then test_players[0..2]

        await game_service.process_leave(owner, test_room_with_players.id, confirm=False)

        assert test_room_with_players.owner is next_owner
        assert next_owner.is_host is True
        assert owner.is_host is False

    async def test_process_leave__owner_leaving_active_game_reassigns_ownership(self, prepared_game, game_service):
        await game_service.start_first_round(prepared_game.room_id)
        owner = prepared_game.room.owner
        next_owner = prepared_game.room.players[1]

        await game_service.process_leave(owner, prepared_game.room_id, confirm=True)

        assert prepared_game.room.owner is next_owner
        assert next_owner.is_host is True
        assert owner.is_host is False

        game_service.game_manager.clear_room_tasks(prepared_game.room_id)

    async def test_process_leave__owner_leaving_broadcasts_new_owner_id(self, test_room_with_players, game_service):
        owner = test_room_with_players.owner
        next_owner = test_room_with_players.players[1]

        game_service.connection_manager.broadcast_to_players = AsyncMock()
        game_service.connection_manager.send_personal_json = AsyncMock()

        await game_service.process_leave(owner, test_room_with_players.id, confirm=False)

        player_left_payloads = [
            call.args[1]
            for call in game_service.connection_manager.broadcast_to_players.await_args_list
            if call.args[1]["event"] == WebsocketEvents.PLAYER_LEFT_ROOM.value
        ]
        assert len(player_left_payloads) == 1
        assert player_left_payloads[0]["payload"]["new_owner_id"] == next_owner.id

    async def test_phase_timer__uses_configured_round_time_limit(self, prepared_game, game_service):
        prepared_game.settings.round_time_limit = 90
        real_sleep = asyncio.sleep
        recorded_timeouts = []

        async def fake_sleep(seconds):
            recorded_timeouts.append(seconds)
            await real_sleep(0)

        with patch("app.services.game_service.asyncio.sleep", side_effect=fake_sleep):
            await game_service.start_first_round(prepared_game.room_id)
            await real_sleep(0)  # let the phase_timer task run up to (and record) its sleep call

        assert recorded_timeouts == [90]

        game_service.game_manager.clear_room_tasks(prepared_game.room_id)

    async def test_phase_timer__settings_change_after_start_does_not_affect_running_round(
        self, prepared_game, game_service
    ):
        await game_service.start_first_round(prepared_game.room_id)

        await game_service.change_game_settings(
            room_id=prepared_game.room_id,
            player_id=prepared_game.room.owner_id,
            data=GameSettingsSchema(round_time_limit=120, max_rounds=None, score_to_win=None),
        )

        # change_game_settings replaced room.settings with a new object, but
        # game.settings still points at the object captured in prepare_game.
        assert prepared_game.room.settings.round_time_limit == 120
        assert prepared_game.settings.round_time_limit == 60

        for player in prepared_game.room.players:
            if player is not prepared_game.current_round.leader:
                await game_service.player_select_card(prepared_game.room_id, player.id, player.handed_cards[0].id)

        winner = next(p for p in prepared_game.room.players if p is not prepared_game.current_round.leader)
        winner_card_id = prepared_game.current_round.player_choices[winner.id].id
        prepared_game.current_round.state = RoundState.LEADER_CHOOSING

        real_sleep = asyncio.sleep
        recorded_timeouts = []

        async def fake_sleep(seconds):
            recorded_timeouts.append(seconds)
            await real_sleep(0)

        with patch("app.services.game_service.asyncio.sleep", side_effect=fake_sleep):
            await game_service.leader_choose_winner(prepared_game.room_id, winner_card_id)
            await real_sleep(0)  # let round 2's phase_timer task reach its sleep call

        assert prepared_game.current_round.round_number == 2
        assert 60 in recorded_timeouts
        assert 120 not in recorded_timeouts

        game_service.game_manager.clear_room_tasks(prepared_game.room_id)


# class TestCardCooldownSystem:
#     """Test card cooldown and availability system"""

#     # @pytest.mark.asyncio
#     async def test_get_available_meme_cards_no_cooldown(self, game_logic, game_with_cards):
#         """Test getting available meme cards with no cooldown"""
#         game_with_cards.round_number = 5
#         game_with_cards.meme_deck = [
#             MemeCard(id=1, image_url="test1.jpg", round_to_return=3),  # Available
#             MemeCard(id=2, image_url="test2.jpg", round_to_return=6),  # Not available
#             MemeCard(id=3, image_url="test3.jpg", round_to_return=None),  # Never used
#         ]

#         available = await game_logic.get_available_meme_cards(game_with_cards)

#         assert len(available) == 2
#         assert available[0].id == 1
#         assert available[1].id == 3

#     # @pytest.mark.asyncio
#     async def test_get_available_situation_cards_with_cooldown(self, game_logic, game_with_cards):
#         """Test getting available situation cards with cooldown"""
#         game_with_cards.round_number = 15
#         game_with_cards.situation_deck = [
#             SituationCard(id=1, text="Test 1", round_to_return=10),  # Available
#             SituationCard(id=2, text="Test 2", round_to_return=20),  # Not available
#             SituationCard(id=3, text="Test 3", round_to_return=None),  # Never used
#         ]

#         available = await game_logic.get_available_situation_cards(game_with_cards)

#         assert len(available) == 2
#         assert available[0].id == 1
#         assert available[1].id == 3


# Note: the game-end-condition tests formerly sketched here now live in
# TestGameLogic above (test_should_end_game__* / test_leader_choose_winner__ends_game_on_*),
# written against the actual GameService._should_end_game shape rather than this stale skeleton.


# class TestEdgeCases:
#     """Test various edge cases and error conditions"""

#     # @pytest.mark.asyncio
#     async def test_hand_out_one_card_leader_excluded(self, game_logic, game_with_cards, players):
#         """Test that leader doesn't get a card when handing out one card"""
#         game_with_cards.room.players = players[:3]
#         game_with_cards.leader_index = 0
#         leader_initial_cards = len(players[0].handed_cards)

#         await game_logic.hand_out_one_card(game_with_cards)

#         # Leader should not get a new card
#         assert len(players[0].handed_cards) == leader_initial_cards
#         # Other players should get cards
#         for player in players[1:3]:
#             assert len(player.handed_cards) > 0

#     # @pytest.mark.asyncio
#     async def test_choose_leader_rotation(self, game_logic, game_with_cards, players):
#         """Test leader rotation through all players"""
#         game_with_cards.room.players = players[:3]
#         game_with_cards.leader_index = 0

#         # Test rotation
#         for i in range(3):
#             leader = await game_logic.choose_leader(game_with_cards)
#             expected_leader = players[(i + 1) % 3]
#             assert leader == expected_leader
#             assert game_with_cards.leader_index == (i + 1) % 3

#     # @pytest.mark.asyncio
#     async def test_end_card_selection_phase_all_players_chosen(self, game_logic, game_with_cards, players):
#         """Test automatic end of card selection when all players choose"""
#         game_with_cards.room.players = players[:3]
#         game_with_cards.current_round = GameRound(
#             round_number=1,
#             leader=players[0],
#             situation_card=SituationCard(id=1, text="Test situation")
#         )
#         game_with_cards.current_round.state = RoundState.CHOOSING_CARDS

#         # Simulate all non-leader players choosing cards
#         for player in players[1:3]:
#             game_with_cards.current_round.player_choices[player.id] = MemeCard(id=1, image_url="test.jpg")

#         # This should trigger automatic end of card selection
#         await game_logic.end_card_selection_phase(game_with_cards)

#         assert game_with_cards.current_round.state == RoundState.LEADER_CHOOSING
#         assert game_with_cards.state == GameState.ROUND_ENDING

#     # @pytest.mark.asyncio
#     async def test_cleanup_room_removes_all_data(self, game_logic, room, players):
#         """Test that room cleanup removes all associated data"""
#         game_logic.game_manager.active_rooms[room.id] = room
#         game_logic.game_manager.active_games[room.id] = Game(room=room)
#         game_logic.game_manager.player_connections = {p.id: room.id for p in players}

#         await game_logic.cleanup_room(room.id)

#         assert room.id not in game_logic.game_manager.active_rooms
#         assert room.id not in game_logic.game_manager.active_games
#         assert all(room.id not in game_logic.game_manager.player_connections.values())

#     # @pytest.mark.asyncio
#     async def test_delayed_cleanup(self, game_logic, room):
#         """Test delayed cleanup functionality"""
#         game_logic.game_manager.active_rooms[room.id] = room

#         # Start delayed cleanup
#         task = asyncio.create_task(game_logic.delayed_cleanup(room.id, delay_seconds=0.1))

#         # Room should still exist immediately
#         assert room.id in game_logic.game_manager.active_rooms

#         # Wait for cleanup
#         await task

#         # Room should be cleaned up
#         assert room.id not in game_logic.game_manager.active_rooms


# class TestConcurrentOperations:
#     """Test concurrent operations and race conditions"""

#     # @pytest.mark.asyncio
#     async def test_concurrent_card_selections(self, game_logic, game_with_cards, players):
#         """Test concurrent card selections from multiple players"""
#         game_with_cards.room.players = players[:3]
#         game_with_cards.current_round = GameRound(
#             round_number=1,
#             leader=players[0],
#             situation_card=SituationCard(id=1, text="Test situation")
#         )
#         game_with_cards.current_round.state = RoundState.CHOOSING_CARDS

#         # Give players cards
#         for i, player in enumerate(players[1:3]):
#             player.handed_cards = [MemeCard(id=i+1, image_url=f"test{i+1}.jpg")]

#         # Simulate concurrent card selections
#         tasks = [
#             game_logic.player_select_card(game_with_cards, players[1].id, 1),
#             game_logic.player_select_card(game_with_cards, players[2].id, 2),
#         ]

#         results = await asyncio.gather(*tasks)

#         # Both should succeed
#         assert all(results)
#         assert len(game_with_cards.current_round.player_choices) == 2

#     # @pytest.mark.asyncio
#     async def test_concurrent_room_joins(self, game_logic, room, players):
#         """Test concurrent room joins"""
#         game_logic.game_manager.active_rooms[room.id] = room

#         # Simulate concurrent joins
#         tasks = [
#             game_logic.join_room(room.id, players[0]),
#             game_logic.join_room(room.id, players[1]),
#         ]

#         results = await asyncio.gather(*tasks, return_exceptions=True)

#         # At least one should succeed, but not both if they have same username
#         assert any(result is True for result in results if not isinstance(result, Exception))
