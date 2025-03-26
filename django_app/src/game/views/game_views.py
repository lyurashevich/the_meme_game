from typing import Optional

from django.http import JsonResponse
from game.models.game_models import Game, GameParticipant, GameSettings
from game.models.game_round_models import GameRound
from game.models.room_models import Room
from game.serializers import (
    GameParticipantSerializer,
    GameRoundSerializer,
    GameSettingsSerializer,
)
from rest_framework import status
from rest_framework.generics import GenericAPIView, get_object_or_404
from rest_framework.mixins import (
    CreateModelMixin,
    DestroyModelMixin,
    ListModelMixin,
    RetrieveModelMixin,
    UpdateModelMixin,
)
from rest_framework.request import Request
from rest_framework.response import Response


def start_game(request: Request, room_id: int) -> JsonResponse:
    """
    Starts a game in the given room. Only the room owner can start the game.
    Returns a JsonResponse with the game ID if the is successfully started.
    """
    room = Room.objects.get(id=room_id)

    if request.user != room.owner:
        return JsonResponse(
            {"error": "you can't start the game as you are not the owner"},
            status=status.HTTP_403_FORBIDDEN,
        )

    game = Game.objects.create(room=room)
    return JsonResponse(
        {"message": "the game started", "game_id": game.id}, status=status.HTTP_200_OK
    )


def end_game(request: Request, game_id: int) -> JsonResponse:
    """
    Ends the game and deletes it from database.
    Return an error message if the game is not found.
    """
    try:
        game = Game.objects.get(id=game_id)
        game.delete()
        return JsonResponse({"message": "the game ended and deleted"})
    except Game.DoesNotExist:
        return JsonResponse(
            {"error": "game not found"}, status=status.HTTP_404_NOT_FOUND
        )


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


class GetGameRoundView(RetrieveModelMixin, UpdateModelMixin, GenericAPIView):
    """
    View to retrieve or update a specific game round.
    """

    queryset = GameRound.objects.all()
    serializer_class = GameRoundSerializer
    lookup_field = "number"

    def get_object(self) -> Optional[GameRound]:
        """
        Retrieves the GameRound object based on 'game_id' and 'number'.
        """
        return get_object_or_404(
            GameRound, game_id=self.kwargs["game_id"], number=self.kwargs["number"]
        )

    def get(self, request: Request, *args, **kwargs) -> Response:
        """
        Retrieves the game round details.
        """
        return self.retrieve(request, *args, **kwargs)

    def patch(self, request: Request, *args, **kwargs) -> Response:
        """
        Partially update the game round settings.
        """
        return self.partial_update(request, *args, **kwargs)


class ListCreateParticipantView(CreateModelMixin, ListModelMixin, GenericAPIView):
    """
    View to list and create game participants.
    """

    queryset = GameParticipant.objects.all()
    serializer_class = GameParticipantSerializer

    def post(self, request: Request, *args, **kwargs) -> Response:
        """
        Create a new game participant.
        """
        return self.create(request, *args, **kwargs)

    def get(self, request: Request, *args, **kwargs) -> Response:
        """
        List all the game participants.
        """
        return self.list(request, *args, **kwargs)


class DetailParticipantView(DestroyModelMixin, RetrieveModelMixin, GenericAPIView):
    """
    Retrieves a specific game participant.
    """

    queryset = GameParticipant.objects.all()
    serializer_class = GameParticipantSerializer

    def get(self, request: Request, *args, **kwargs) -> Response:
        """
        Retrieves a specific game participant.
        """
        return self.retrieve(request, *args, **kwargs)

    def delete(self, request: Request, *args, **kwargs) -> Response:
        """
        Deletes a specific game participant.
        """
        return self.destroy(request, *args, **kwargs)
