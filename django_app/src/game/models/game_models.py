from django.core.validators import MaxValueValidator, MinValueValidator
from django.db import models


class Game(models.Model):
    """
    Represents an active game session associated with room.
    """

    room = models.ForeignKey("Room", on_delete=models.CASCADE, blank=False)


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
