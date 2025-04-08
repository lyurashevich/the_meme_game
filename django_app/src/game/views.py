from game.models import MemeCard, Player, Room, RoomCount, SituationCard
from game.serializers import (
    MemeCardSerializer,
    PlayerSerializer,
    RoomSerializer,
    SituationCardSerializer,
)
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
from rest_framework.views import APIView
from rest_framework_simplejwt.tokens import AccessToken


class MemeCardsListView(ListModelMixin, GenericAPIView):
    queryset = MemeCard.objects.all()
    serializer_class = MemeCardSerializer

    def get(self, request, *args, **kwargs):
        return self.list(request, *args, **kwargs)


class SituationCardsListView(ListModelMixin, GenericAPIView):
    queryset = SituationCard.objects.all()
    serializer_class = SituationCardSerializer

    def get(self, request, *args, **kwargs):
        return self.list(request, *args, **kwargs)


class RoomCreateView(CreateModelMixin, GenericAPIView):
    """
    View to create a new room and to get list of all rooms.
    """

    queryset = Room.objects.all()
    serializer_class = RoomSerializer
    permission_classes = [IsAuthenticated]

    def post(self, request, *args, **kwargs):
        return self.create(request, *args, **kwargs)

    def create(self, request, *args, **kwargs):
        Room.objects.filter(owner=request.user).delete()

        serializer = self.get_serializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        room = serializer.save(owner=request.user)

        token = AccessToken()
        token["room_id"] = str(room.id)

        return Response(
            {**serializer.data, "room_token": str(token)},
            status=status.HTTP_201_CREATED,
        )


class RoomListView(ListModelMixin, GenericAPIView):
    queryset = Room.objects.filter(is_private=False)
    serializer_class = RoomSerializer

    def get(self, request: Request, *args, **kwargs) -> Response:
        """
        Get a list of all rooms.
        """
        return self.list(request, *args, **kwargs)


class PlayerListCreateView(ListModelMixin, CreateModelMixin, GenericAPIView):
    """
    Views to create a new player and to list all players.
    """

    queryset = Player.objects.all()
    serializer_class = PlayerSerializer

    def post(self, request: Request, *args, **kwargs) -> Response:
        player = Player.objects.create_user(**request.data)

        token = AccessToken.for_user(player)

        return Response(
            {
                **PlayerSerializer(player).data,
                "player_token": str(token),
            },
            status=status.HTTP_201_CREATED,
        )

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


class UpdateRoomCountView(APIView):

    def put(self, request, *args, **kwargs):
        active_rooms = request.data.get("active_rooms", 0)

        RoomCount.objects.update_or_create(
            id=1, defaults={"active_rooms": active_rooms}
        )

        return Response({"status:": "success"}, status=status.HTTP_200_OK)
