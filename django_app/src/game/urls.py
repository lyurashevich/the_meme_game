from django.urls import path
from game.views import (
    MemeCardsListView,
    PlayerDetailView,
    PlayerListCreateView,
    RoomCreateView,
    RoomListView,
    SituationCardsListView,
    UpdateRoomCountView,
)

urlpatterns = [
    path("active_rooms/", UpdateRoomCountView.as_view(), name="update-active-rooms"),
    path("cards/meme_cards/", MemeCardsListView.as_view(), name="get-meme-cards"),
    path(
        "cards/situation_cards/",
        SituationCardsListView.as_view(),
        name="get-situation-cards",
    ),
    path("rooms/", RoomCreateView.as_view(), name="create-room"),
    path("rooms/available/", RoomListView.as_view(), name="room-list"),
    path("players/", PlayerListCreateView.as_view(), name="player_list_create"),
    path("player/<int:pk>/", PlayerDetailView.as_view(), name="player_detail"),
]
