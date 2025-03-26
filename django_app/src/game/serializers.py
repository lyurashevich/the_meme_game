from game.models.card_models import Card, DiscardPile, PlayerCard
from game.models.game_models import GameParticipant, GameSettings
from game.models.game_round_models import GameRound
from game.models.player_models import Player
from game.models.room_models import Room
from rest_framework import serializers

# === Player Related ===


class PlayerSerializer(serializers.ModelSerializer):
    class Meta:
        model = Player
        fields = "__all__"


# === Room Related ==


class RoomSerializer(serializers.ModelSerializer):
    class Meta:
        model = Room
        fields = "__all__"
        read_only_fields = ["id", "invitation_link", "owner"]


# === Card Related ===


class CardSerializer(serializers.ModelSerializer):
    class Meta:
        model = Card
        fields = "__all__"

    def to_representation(self, instance):
        data = super().to_representation(instance)
        if instance.type == "meme":
            data.pop("text")
        elif instance.type == "situation":
            data.pop("image_url")
        return data


class PlayerCardSerializer(serializers.ModelSerializer):
    class Meta:
        model = PlayerCard
        fields = "__all__"


class DiscardPileSerializer(serializers.ModelSerializer):
    class Meta:
        model = DiscardPile
        fields = "__all__"


# === Game Related ===


class GameParticipantSerializer(serializers.ModelSerializer):
    class Meta:
        model = GameParticipant
        fields = "__all__"


class GameSettingsSerializer(serializers.ModelSerializer):
    class Meta:
        model = GameSettings
        fields = "__all__"


class GameRoundSerializer(serializers.ModelSerializer):
    class Meta:
        model = GameRound
        fields = "__all__"
