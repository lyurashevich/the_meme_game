from game.models import MemeCard, Player, Room, RoomCount, SituationCard
from rest_framework import serializers


class PlayerSerializer(serializers.ModelSerializer):
    class Meta:
        model = Player
        fields = "__all__"


class RoomSerializer(serializers.ModelSerializer):
    class Meta:
        model = Room
        fields = "__all__"
        read_only_fields = ["id", "invitation_link", "owner"]


class MemeCardSerializer(serializers.ModelSerializer):
    class Meta:
        model = MemeCard
        fields = "__all__"


class SituationCardSerializer(serializers.ModelSerializer):
    class Meta:
        model = SituationCard
        fields = "__all__"


class RoomCountSerializer(serializers.ModelSerializer):
    class Meta:
        model = RoomCount
        fileds = "__all__"
