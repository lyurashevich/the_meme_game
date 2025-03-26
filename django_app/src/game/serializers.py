from game.models import (
    Card,
    DiscardPile,
    GameParticipant,
    GameRound,
    GameSettings,
    Player,
    PlayerCard,
    Room,
)
from rest_framework import serializers


class PlayerSerializer(serializers.ModelSerializer):
    class Meta:
        model = Player
        fields = ["username"]
        extra_kwargs = {
            "username": {"required": False},
        }


class RoomSerializer(serializers.ModelSerializer):
    class Meta:
        model = Room
        fields = ["id", "name", "max_players", "owner", "invitation_link"]
        read_only_fields = ["id", "invitation_link", "owner"]


class CardSerializer(serializers.ModelSerializer):
    class Meta:
        model = Card
        fields = ["id", "type", "text", "image_url"]

    def to_representation(self, instance):
        data = super().to_representation(instance)
        if instance.type == "meme":
            data.pop("text")
        elif instance.type == "situation":
            data.pop("image_url")
        return data


class GameParticipantSerializer(serializers.ModelSerializer):
    class Meta:
        model = GameParticipant
        fields = ["id", "game", "player", "score"]


class GameSettingsSerializer(serializers.ModelSerializer):
    class Meta:
        model = GameSettings
        fields = ["id", "game", "time_per_turn", "time_to_choose_winner", "score_limit"]


class GameRoundSerializer(serializers.ModelSerializer):
    class Meta:
        model = GameRound
        fields = "__all__"


class PlayerCardSerializer(serializers.ModelSerializer):
    class Meta:
        model = PlayerCard
        fields = "__all__"


class DiscardPileSerializer(serializers.ModelSerializer):
    class Meta:
        model = DiscardPile
        fields = "__all__"
