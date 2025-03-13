from rest_framework import serializers

from .models import ApiModel


class TestSerializer(serializers.ModelSerializer):
    class Meta:
        model = ApiModel
        fields = ["name"]
