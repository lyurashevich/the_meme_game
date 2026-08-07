from app.game.enums import WebsocketEvents
from app.services.room_service import RoomService


class TestRoomServiceMessages:
    async def test_build_room_created_message(self, test_room):
        audience = ["socket-1", "socket-2"]

        recipients, payload = RoomService.build_room_created_message(test_room, audience)

        assert recipients == audience
        assert payload == {
            "event": WebsocketEvents.ROOM_CREATED.value,
            "payload": {"room_id": test_room.id, "room_name": test_room.name},
        }

    async def test_build_join_room_messages(self, test_room_with_players, test_players):
        room = test_room_with_players
        joining_player = test_players[0]

        messages = RoomService.build_join_room_messages(room, joining_player)

        assert len(messages) == 2

        you_joined_recipients, you_joined_payload = messages[0]
        assert you_joined_recipients == [joining_player.id]
        assert you_joined_payload == {
            "event": WebsocketEvents.YOU_JOINED_THE_ROOM.value,
            "payload": {
                "room_id": room.id,
                "room_name": room.name,
                "players": [{"id": p.id, "username": p.username} for p in room.players],
            },
        }

        player_joined_recipients, player_joined_payload = messages[1]
        assert joining_player.id not in player_joined_recipients
        assert set(player_joined_recipients) == {p.id for p in room.players if p.id != joining_player.id}
        assert player_joined_payload == {
            "event": WebsocketEvents.PLAYER_JOINED_ROOM.value,
            "payload": {"player_id": joining_player.id, "username": joining_player.username},
        }
