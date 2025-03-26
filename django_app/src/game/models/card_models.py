from django.db import models
from game.models.game_models import Game, GameParticipant


class Card(models.Model):
    """
    Represents a card in the game. It can be either a 'meme' or a 'situation'.
    """

    TYPE_CHOICES = [
        ("meme", "Meme"),
        ("situation", "Situation"),
    ]
    type = models.CharField(max_length=10, choices=TYPE_CHOICES)
    text = models.TextField(blank=True, null=True)  # for situations
    image_url = models.URLField(blank=True, null=True)  # for memes


class PlayerCard(models.Model):
    """
    Represents cards currently held by a player during a game.
    """

    participant = models.ForeignKey(GameParticipant, on_delete=models.CASCADE)
    game = models.ForeignKey(Game, on_delete=models.CASCADE)
    card = models.ForeignKey(Card, on_delete=models.CASCADE)


class DiscardPile(models.Model):
    """
    Represents temporarily discarded cards for particular game.

    Cards in the discard pile return to the game after a certain number of rounds.

    Key logic:
     - 'round_expires' defines the round number when the card will become available again.
     - The card remains unavailable until 'current_round < round_expires'

     Example:
     - A card is discarded in round 5 and should be unavailable for 10 rounds.
     - Card becomes available again in round 15 (5 + 10).
    """

    game = models.ForeignKey(Game, on_delete=models.CASCADE)
    card = models.ForeignKey(Card, on_delete=models.CASCADE)
    round_expires = models.IntegerField()
