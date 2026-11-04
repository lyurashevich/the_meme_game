from app.services.snapshots import CHAT_HISTORY_LIMIT


class TestRoomServiceChat:
    async def test_add_chat_message(self, test_room, test_player, room_service):
        message = await room_service.add_chat_message(test_room.id, test_player, "hi")

        assert message["player_id"] == test_player.id
        assert message["username"] == test_player.username
        assert message["text"] == "hi"
        assert message["timestamp"]
        assert test_room.messages == [message]

    async def test_only_latest_messages_are_kept(self, test_room, test_player, room_service):
        for i in range(CHAT_HISTORY_LIMIT + 5):
            await room_service.add_chat_message(test_room.id, test_player, str(i))

        assert len(test_room.messages) == CHAT_HISTORY_LIMIT
        assert test_room.messages[0]["text"] == "5"
        assert test_room.messages[-1]["text"] == str(CHAT_HISTORY_LIMIT + 4)
