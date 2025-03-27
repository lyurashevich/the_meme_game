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
    """
    Represents a player in a game.

    - 'id': A unique identifier for the player.
    - 'username': The player's username.
    """

    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    username = models.CharField(max_length=50, blank=True, null=True, unique=True)

    objects = PlayerManager()

    USERNAME_FIELD = "username"
    REQUIRED_FIELDS: list[str] = []

    def check_password(self, raw_password) -> bool:
        """
        Always returns False as the password is disabled.
        """
        return False
