from typing import Optional

from game.game_logic import GameManager
from game.models.game_models import Game, GameSettings
from game.serializers import GameSerializer, GameSettingsSerializer
from rest_framework import status
from rest_framework.decorators import api_view
from rest_framework.generics import GenericAPIView, get_object_or_404
from rest_framework.mixins import (
    CreateModelMixin,
    DestroyModelMixin,
    ListModelMixin,
    RetrieveModelMixin,
    UpdateModelMixin,
)
from rest_framework.permissions import IsAuthenticated
from rest_framework.request import Request
from rest_framework.response import Response


@api_view(["POST"])
def start_game(request, game_id):
    try:
        game = Game.objects.get(id=game_id)
    except Game.DoesNotExist:
        return Response({"error:": "game not found"}, status=status.HTTP_404_NOT_FOUND)

    if game.owner != request.user:
        return Response(
            {"error": "only owner can start the game"}, status=status.HTTP_403_FORBIDDEN
        )

    manager = GameManager(game)
    try:
        manager.start_game()
        return Response({"status": "ok"})
    except ValueError as e:
        return Response({"error:": str(e)}, status=status.HTTP_400_BAD_REQUEST)


class GameListCreate(ListModelMixin, CreateModelMixin, GenericAPIView):
    """
    View to create a new room and to get list of all rooms.
    """

    queryset = Game.objects.all()
    serializer_class = GameSerializer
    permission_classes = [IsAuthenticated]

    def post(self, request: Request, *args, **kwargs) -> Response:
        """
        Create a new room with provided data.
        """
        return self.create(request, *args, **kwargs)

    def get(self, request: Request, *args, **kwargs) -> Response:
        """
        Get a list of all rooms.
        """
        return self.list(request, *args, **kwargs)

    def perform_create(self, serializer) -> None:
        """
        Auto-set the current user as the room owner upon creation.
        """
        serializer.save(owner=self.request.user)


class GameDetailView(
    RetrieveModelMixin, UpdateModelMixin, DestroyModelMixin, GenericAPIView
):
    """
    Views to get a specific room by ID, to delete or partial update the room's data.
    """

    queryset = Game.objects.all()
    serializer_class = GameSerializer
    permission_classes = [IsAuthenticated]

    def get(self, request: Request, *args, **kwargs) -> Response:
        """
        Get a room by ID.
        """
        return self.retrieve(request, *args, **kwargs)

    def delete(self, request: Request, *args, **kwargs) -> Response:
        """
        Delete a room by ID.
        """
        return self.destroy(request, *args, **kwargs)

    def patch(self, request: Request, *args, **kwargs) -> Response:
        """
        Partial update the room data.
        """
        return self.partial_update(request, *args, **kwargs)


class DetailSettingsView(
    RetrieveModelMixin, CreateModelMixin, UpdateModelMixin, GenericAPIView
):
    """
    View to retrieve, create or update game settings.
    """

    queryset = GameSettings.objects.all()
    serializer_class = GameSettingsSerializer
    lookup_field = "game_id"

    def get_object(self) -> Optional[GameSettings]:
        """
        Retrieves the GameSettings objet based on the 'game_id' parameter.
        """
        return get_object_or_404(GameSettings, game_id=self.kwargs["game_id"])

    def get(self, request: Request, *args, **kwargs) -> Response:
        """
        Retrieves the game settings.
        """
        return self.retrieve(request, *args, **kwargs)

    def patch(self, request: Request, *args, **kwargs) -> Response:
        """
        Partially updates the game settings.
        """
        return self.partial_update(request, *args, **kwargs)
