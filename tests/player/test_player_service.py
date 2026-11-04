from app.schemas.players import BasePlayerProfileSchema


class TestPlayerService:

    async def test_update_player_profile__username(self, test_player, player_service, outbox):
        test_player.avatar_id = "avatar_id"

        await player_service.update_player_profile(test_player.id, BasePlayerProfileSchema(username="new"))

        assert test_player.username == "new"
        assert test_player.avatar_id == "avatar_id"
        assert outbox == []  # notifying the room is up to the caller

    async def test_update_player_profile__avatar(self, test_player, player_service):
        await player_service.update_player_profile(test_player.id, BasePlayerProfileSchema(avatar_id="cat"))

        assert test_player.avatar_id == "cat"
        assert test_player.username == "Lisaveta"
