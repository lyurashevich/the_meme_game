import uuid

from django.db import models


class Player(models.Model):
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    username = models.CharField(max_length=50, blank=True)
    created_at = models.DateTimeField(auto_now_add=True)

    def save(self, *args, **kwargs):
        if not self.username:
            self.username = f"player{self.id}"
        super().save(*args, **kwargs)


class TooManyPlayersError(Exception):
    pass


class Room(models.Model):
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    name = models.CharField(max_length=50, blank=True)
    players = models.ManyToManyField(Player, related_name="rooms", blank=True)
    max_players = models.IntegerField(default=10)
    owner = models.ForeignKey(Player, on_delete=models.CASCADE, null=False, blank=False)
    invitation_link = models.URLField(blank=True, null=True)

    def save(self, *args, **kwargs):
        if not self.name:
            self.name = f"room{self.id}"
        super().save(*args, **kwargs)

        if self.owner not in self.players.all():
            self.players.add(self.owner)

    def add_player(self, player):
        if self.players.count() >= self.max_players:
            raise TooManyPlayersError("the room is already full")
        self.players.add(player)


class Card(models.Model):
    TYPE_CHOICES = [
        ("meme", "Meme"),
        ("situation", "Situation"),
    ]
    type = models.CharField(max_length=10, choices=TYPE_CHOICES)
    text = models.TextField(blank=True, null=True)  # for situations
    image_url = models.URLField(blank=True, null=True)  # for memes


class Game(models.Model):
    room = models.ForeignKey("Room", on_delete=models.CASCADE, blank=False)

    def __str__(self):
        return f"game in room {self.room.name}"


class GameParticipant(models.Model):
    game = models.ForeignKey(
        "Game", on_delete=models.CASCADE, related_name="participants"
    )
    player = models.ForeignKey("Player", on_delete=models.CASCADE, related_name="games")
    score = models.IntegerField(default=0)

    class Meta:
        unique_together = ("game", "player")
