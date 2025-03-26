import uuid

from django.db import models
from game.models.player_models import Player


class TooManyPlayersError(Exception):
    pass


class Room(models.Model):
    """
    Represents a game room players can join.

    - 'id': A unique identifier for the room.
    - 'name': The name of the room. If not provided will be generated automatically.
    - 'players': A foreign key to the player in the room.
    - 'max_players': The maximum number of player allowed in the room.
    - 'owner: The player who owns the room.
    - 'invitation_link': A link that can be shared to invite players to the room.
    """

    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    name = models.CharField(max_length=50, blank=True)
    players = models.ManyToManyField(Player, related_name="rooms", blank=True)
    max_players = models.IntegerField(default=10)
    owner = models.ForeignKey(Player, on_delete=models.CASCADE, null=False, blank=False)
    invitation_link = models.URLField(blank=True, null=True)

    def save(self, *args, **kwargs) -> None:
        """
        Saves the room instance and generates default name if it's not provided.
        """

        if not self.name:
            self.name = f"room{self.id}"
        super().save(*args, **kwargs)
