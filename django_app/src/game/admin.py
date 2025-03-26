from django.contrib import admin
from game.models.card_models import Card
from game.models.player_models import Player
from game.models.room_models import Room

admin.site.register(Player)
admin.site.register(Card)
admin.site.register(Room)
