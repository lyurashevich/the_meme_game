import uuid

from django.contrib.auth.base_user import AbstractBaseUser, BaseUserManager
from django.db import models


class PlayerManager(BaseUserManager):
    def create_user(self, username: str | None = None) -> "Player":
        """
        Creates and saves a player with the given username if it is provided.
        If username is not provided, generates a random one.
        """
        if not username:
            user = self.model(username=f"player{uuid.uuid4().hex[:8]}")
        else:
            user = self.model(username=username)
        user.set_unusable_password()
        user.save(using=self._db)
        return user


class Player(AbstractBaseUser):

    id = models.UUIDField(default=uuid.uuid4, unique=True, primary_key=True)
    username = models.CharField(blank=True, null=True, unique=True)

    objects = PlayerManager()

    USERNAME_FIELD = "username"
    REQUIRED_FIELDS: list[str] = []

    def check_password(self, raw_password) -> bool:
        """
        Always returns False as the password is disabled.
        """
        return False


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

    id = models.UUIDField(default=uuid.uuid4, unique=True, primary_key=True)
    name = models.CharField(max_length=50, blank=True)
    max_players = models.IntegerField(default=10)
    owner = models.ForeignKey(Player, on_delete=models.CASCADE)
    invitation_link = models.URLField(blank=True, null=True)
    is_private = models.BooleanField(default=False)

    def save(self, *args, **kwargs) -> None:
        """
        Saves the room instance and generates default name if it's not provided.
        """

        if not self.name:
            self.name = f"room{self.id}"

        super().save(*args, **kwargs)


class MemeCard(models.Model):
    """
    Represents a situation card in the game.
    """

    image_url = models.URLField()


class SituationCard(models.Model):
    """
    Represents a meme card in the game.
    """

    text = models.TextField()
