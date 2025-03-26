from game.models.player_models import Player
from game.serializers import PlayerSerializer
from rest_framework.generics import GenericAPIView
from rest_framework.mixins import (
    CreateModelMixin,
    DestroyModelMixin,
    ListModelMixin,
    RetrieveModelMixin,
    UpdateModelMixin,
)
from rest_framework.request import Request
from rest_framework.response import Response


class PlayerListCreateView(ListModelMixin, CreateModelMixin, GenericAPIView):
    """
    Views to create a new player and to list all players.
    """

    queryset = Player.objects.all()
    serializer_class = PlayerSerializer

    def post(self, request: Request, *args, **kwargs) -> Response:
        """
        Create a new player with provided data.
        """
        return self.create(request, *args, **kwargs)

    def get(self, request: Request, *args, **kwargs) -> Response:
        """
        Retrieve list of all players.
        """
        return self.list(request, *args, **kwargs)


class PlayerDetailView(
    RetrieveModelMixin, UpdateModelMixin, DestroyModelMixin, GenericAPIView
):
    """
    Views to get a specific player, to partial update player's data, to delete player.
    """

    queryset = Player.objects.all()
    serializer_class = PlayerSerializer

    def get(self, request: Request, *args, **kwargs) -> Response:
        """
        Get details of a specific player by ID.
        """
        return self.retrieve(request, *args, **kwargs)

    def delete(self, request: Request, *args, **kwargs) -> Response:
        """
        Delete player by ID.
        """
        return self.destroy(request, *args, **kwargs)

    def patch(self, request: Request, *args, **kwargs) -> Response:
        """
        Partial update player's data.
        """
        return self.partial_update(request, *args, **kwargs)
