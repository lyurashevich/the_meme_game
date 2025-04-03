from django.core.validators import MaxValueValidator, MinValueValidator
from django.db import models
from game.models.player_models import Player


class TooManyPlayersError(Exception):
    pass


class Game(models.Model):
    """
    Represents a game room players can join.

    - 'id': A unique identifier for the room.
    - 'name': The name of the room. If not provided will be generated automatically.
    - 'players': A foreign key to the player in the room.
    - 'max_players': The maximum number of player allowed in the room.
    - 'owner: The player who owns the room.
    - 'invitation_link': A link that can be shared to invite players to the room.
    """

    id = models.BigAutoField(primary_key=True)
    name = models.CharField(max_length=50, blank=True)
    max_players = models.IntegerField(default=10)
    owner = models.ForeignKey(Player, on_delete=models.CASCADE, null=True)
    invitation_link = models.URLField(blank=True, null=True)
    is_private = models.BooleanField(default=False)

    def save(self, *args, **kwargs) -> None:
        """
        Saves the room instance and generates default name if it's not provided.
        """

        if not self.name:
            self.name = f"room{self.id}"

        is_new = self._state.adding
        super().save(*args, **kwargs)

        if is_new:
            GameParticipant.objects.get_or_create(game=self, player=self.owner)

    def add_player(self, player):
        if self.participants.count() >= self.max_players:
            raise TooManyPlayersError("the room is already full")
        GameParticipant.objects.create(game=self, player=player)


class GameParticipant(models.Model):
    """
    Represents a player participating in a specific game session.

    Each player can only participate in a game once.
    """

    game = models.ForeignKey(
        "Game", on_delete=models.CASCADE, related_name="participants"
    )
    player = models.ForeignKey("Player", on_delete=models.CASCADE, related_name="games")
    score = models.IntegerField(default=0)

    class Meta:
        unique_together = ("game", "player")


class GameSettings(models.Model):
    """
    Stores game configuration settings for a specific game session.

    - 'time_per_turn': Time (in seconds) each player has for their turn (for choosing a card).
    - 'time_to_choose_winner': Time (in seconds) the leader has to select winner.
    - 'score_limit': The maximum score required to win the game. Once the 'score_limit' is reached the game ends.
    """

    game = models.ForeignKey(Game, on_delete=models.CASCADE)
    time_per_turn = models.PositiveIntegerField(
        default=60, validators=[MinValueValidator(30), MaxValueValidator(120)]
    )
    time_to_choose_winner = models.PositiveIntegerField(
        default=60, validators=[MinValueValidator(30), MaxValueValidator(120)]
    )
    score_limit = models.PositiveIntegerField(default=0)  # 0 means no limit
