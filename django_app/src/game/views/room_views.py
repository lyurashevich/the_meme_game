from game.models.room_models import Room
from game.serializers import RoomSerializer
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


class RoomListCreate(ListModelMixin, CreateModelMixin, GenericAPIView):
    """
    View to create a new room and to get list of all rooms.
    """

    queryset = Room.objects.all()
    serializer_class = RoomSerializer
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


class RoomDetailView(
    RetrieveModelMixin, UpdateModelMixin, DestroyModelMixin, GenericAPIView
):
    """
    Views to get a specific room by ID, to delete or partial update the room's data.
    """

    queryset = Room.objects.all()
    serializer_class = RoomSerializer
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
