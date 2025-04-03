from game.models.game_models import Game, GameSettings
from game.models.player_models import Player
from rest_framework import serializers

# === Player Related ===


class PlayerSerializer(serializers.ModelSerializer):
    class Meta:
        model = Player
        fields = "__all__"


# === Room Related ==


class GameSerializer(serializers.ModelSerializer):
    class Meta:
        model = Game
        fields = "__all__"
        read_only_fields = ["id", "invitation_link", "owner"]


# === Game Related ===


class GameSettingsSerializer(serializers.ModelSerializer):
    class Meta:
        model = GameSettings
        fields = "__all__"
