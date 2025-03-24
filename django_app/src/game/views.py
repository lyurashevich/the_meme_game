from django.http import JsonResponse
from game.models import Card, Game, Player, Room
from game.serializers import CardSerializer, PlayerSerializer, RoomSerializer
from rest_framework import status
from rest_framework.generics import GenericAPIView
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

####################################################
#                     PLAYER                       #
####################################################


class PlayerListCreateView(ListModelMixin, CreateModelMixin, GenericAPIView):
    queryset = Player.objects.all()
    serializer_class = PlayerSerializer

    def post(self, request, *args, **kwargs):
        return self.create(request, *args, **kwargs)

    def get(self, request, *args, **kwargs):
        return self.list(request, *args, **kwargs)


class PlayerDetailView(
    RetrieveModelMixin, UpdateModelMixin, DestroyModelMixin, GenericAPIView
):
    queryset = Player.objects.all()
    serializer_class = PlayerSerializer

    def get(self, request, *args, **kwargs):
        return self.retrieve(request, *args, **kwargs)

    def delete(self, request, *args, **kwargs):
        return self.destroy(request, *args, **kwargs)

    def patch(self, request, *args, **kwargs):
        return self.partial_update(request, *args, **kwargs)


####################################################
#                       ROOM                       #
####################################################


class RoomListCreate(ListModelMixin, CreateModelMixin, GenericAPIView):
    queryset = Room.objects.all()
    serializer_class = RoomSerializer
    permission_classes = [IsAuthenticated]

    def post(self, request, *args, **kwargs):
        return self.create(request, *args, **kwargs)

    def get(self, request, *args, **kwargs):
        return self.list(request, *args, **kwargs)

    def perform_create(self, serializer) -> None:
        """
        auto-sets the current user as the room owner upon creation
        """
        serializer.save(owner=self.request.user)


class RoomDetailView(
    RetrieveModelMixin, UpdateModelMixin, DestroyModelMixin, GenericAPIView
):
    queryset = Room.objects.all()
    serializer_class = RoomSerializer
    permission_classes = [IsAuthenticated]

    def get(self, request, *args, **kwargs):
        return self.retrieve(request, *args, **kwargs)

    def delete(self, request, *args, **kwargs):
        return self.destroy(request, *args, **kwargs)

    def patch(self, request, *args, **kwargs):
        return self.partial_update(request, *args, **kwargs)


####################################################
#                       CARDS                      #
####################################################


class StartGameHandOutView(GenericAPIView):
    """
    hands out 6 random card in the beginning of the game
    """

    serializer_class = CardSerializer

    def get(self, request: Request) -> Response:
        cards = list(Card.objects.filter(type="meme").order_by("?")[:6])
        return Response(CardSerializer(cards, many=True).data)


class HandOutOneCardView(GenericAPIView):
    """
    gives one meme or one situation card depending on query params
    """

    serializer_class = CardSerializer

    def get(self, request: Request) -> Response:
        card_type = request.query_params.get("type")

        if card_type not in ["meme", "situation"]:
            return Response(
                {"error": "invalid card type"}, status=status.HTTP_400_BAD_REQUEST
            )

        card = Card.objects.filter(type=card_type).order_by("?").first()

        return Response(CardSerializer(card).data)


####################################################
#                       GAME                       #
####################################################


def start_game(request: Request, room_id: int) -> JsonResponse:
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
    try:
        game = Game.objects.get(id=game_id)
        game.delete()
        return JsonResponse({"message": "the game ended and deleted"})
    except Game.DoesNotExist:
        return JsonResponse(
            {"error": "game not found"}, status=status.HTTP_404_NOT_FOUND
        )
