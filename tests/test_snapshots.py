"""What each player gets to see: the snapshot is personal and must not leak hidden information."""

import pytest

from app.game.dataclasses import Player, Room
from app.game.enums import GameState, RoundState
from app.services.snapshots import (
    CHAT_HISTORY_LIMIT,
    build_game_ended,
    build_room_state,
    build_rooms_list,
)


@pytest.fixture
async def started_game(prepared_game, game_service):
    await game_service.start_first_round(prepared_game.room_id)
    yield prepared_game
    game_service.game_manager.clear_room_tasks(prepared_game.room_id)


def card_ids(cards):
    return [card["id"] for card in cards]


class TestRoomState:
    def test_lobby(self, test_room_with_players):
        room = test_room_with_players
        owner = room.owner

        state = build_room_state(room, None, owner)

        assert state["room"] == {
            "id": room.id,
            "name": room.name,
            "owner_id": owner.id,
            "max_players": room.max_players,
            "settings": {"round_time_limit": 60, "max_rounds": None, "score_to_win": None},
        }
        assert [p["id"] for p in state["players"]] == [p.id for p in room.players]
        assert state["players"][0] == {
            "id": owner.id,
            "username": owner.username,
            "avatar_id": owner.avatar_id,
            "score": 0,
            "is_connected": True,
        }
        assert state["game"] is None
        assert "chat" not in state

    def test_chat_history_only_when_asked_and_capped(self, test_room, test_player):
        test_room.messages = [{"text": str(i)} for i in range(CHAT_HISTORY_LIMIT + 10)]

        state = build_room_state(test_room, None, test_player, chat=test_room.messages)

        assert len(state["chat"]) == CHAT_HISTORY_LIMIT
        assert state["chat"][-1] == {"text": str(CHAT_HISTORY_LIMIT + 9)}

    def test_finished_game_is_shown_as_lobby(self, started_game):
        started_game.state = GameState.FINISHED

        assert build_room_state(started_game.room, started_game, started_game.room.owner)["game"] is None

    def test_choosing_cards_each_player_sees_only_their_own_hand(self, started_game, game_service):
        room = started_game.room
        leader, first, second = room.players[0], room.players[1], room.players[2]

        for player in room.players:
            game = build_room_state(room, started_game, player)["game"]
            assert card_ids(game["my_hand"]) == [card.id for card in player.hand_cards]
            assert game["round_number"] == 1
            assert game["round_state"] == RoundState.CHOOSING_CARDS.value
            assert game["leader_id"] == leader.id
            assert game["situation"]["text"] == started_game.current_round.situation_card.text

        # nobody can find another player's hand anywhere in their snapshot
        first_snapshot = repr(build_room_state(room, started_game, first))
        assert second.hand_cards
        assert all(f"'{card.image_url}'" not in first_snapshot for card in second.hand_cards)

    async def test_choosing_cards_shows_who_played_but_not_what(self, started_game, game_service):
        room = started_game.room
        first, second = room.players[1], room.players[2]
        played = first.hand_cards[0]
        await game_service.player_select_card(started_game.room_id, first.id, played.id)

        mine = build_room_state(room, started_game, first)["game"]
        theirs = build_room_state(room, started_game, second)["game"]

        assert mine["submitted_player_ids"] == theirs["submitted_player_ids"] == [first.id]
        assert mine["my_selected_card_id"] == played.id
        assert theirs["my_selected_card_id"] is None
        assert mine["table"] == theirs["table"] == []

    async def test_leader_choosing_shows_anonymous_table(self, started_game, game_service):
        room = started_game.room
        for player in room.players[1:]:
            await game_service.player_select_card(started_game.room_id, player.id, player.hand_cards[-1].id)

        played = started_game.current_round.player_choices
        for player in room.players:
            game = build_room_state(room, started_game, player)["game"]
            assert game["round_state"] == RoundState.LEADER_CHOOSING.value
            assert card_ids(game["table"]) == sorted(card.id for card in played.values())
            assert all(set(entry) == {"id", "image_url"} for entry in game["table"])  # no authors
            assert game["winner"] is None

    async def test_winner_is_shown_after_leader_choice(self, started_game, game_service):
        room = started_game.room
        for player in room.players[1:]:
            await game_service.player_select_card(started_game.room_id, player.id, player.hand_cards[0].id)
        winner = room.players[2]
        winning_card = started_game.current_round.player_choices[winner.id]

        await game_service.leader_choose_winner(started_game.room_id, room.owner.id, winning_card.id)

        game = build_room_state(room, started_game, room.players[1])["game"]
        assert game["winner"] == {"player_id": winner.id, "card_id": winning_card.id}
        assert (
            next(p for p in build_room_state(room, started_game, winner)["players"] if p["id"] == winner.id)["score"]
            == 1
        )


class TestRoomsList:
    def test_public_rooms_with_status(self, started_game, test_player):
        waiting_room = Room(owner=Player(username="Host"), max_players=5)
        private_room = Room(owner=Player(username="Secret"), is_private=True)

        rooms_list = build_rooms_list(
            [started_game.room, waiting_room, private_room], {started_game.room_id: started_game}
        )

        assert rooms_list == [
            {
                "id": started_game.room_id,
                "name": started_game.room.name,
                "players_count": 4,
                "max_players": 10,
                "status": "playing",
            },
            {
                "id": waiting_room.id,
                "name": waiting_room.name,
                "players_count": 1,
                "max_players": 5,
                "status": "waiting",
            },
        ]


class TestGameEnded:
    def test_winner_ids_include_ties(self, test_room):
        payload = build_game_ended(test_room, "limit_reached", {"a": 3, "b": 3, "c": 1})

        assert payload == {
            "room_id": test_room.id,
            "reason": "limit_reached",
            "final_scores": {"a": 3, "b": 3, "c": 1},
            "winner_ids": ["a", "b"],
        }

    def test_no_winner_without_points(self, test_room):
        assert build_game_ended(test_room, "owner_ended", {"a": 0, "b": 0})["winner_ids"] == []
