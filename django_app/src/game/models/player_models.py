import uuid

from django.db import models


class Player(models.Model):
    """
    Represents a player in a game.

    - 'id': A unique identifier for the player.
    - 'username': The player's username. If not provided, it will be generated
    based on their ID.
    """

    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    username = models.CharField(max_length=50, blank=True)
    created_at = models.DateTimeField(auto_now_add=True)

    def save(self, *args, **kwargs) -> None:
        """
        Saves the player instance with the default username if username is not
        provided.
        """
        if not self.username:
            self.username = f"player{self.id}"
        super().save(*args, **kwargs)
