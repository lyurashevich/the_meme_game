from django.urls import path
from game.views import (
    DetailParticipantView,
    DetailSettingsView,
    HandOutOneCardView,
    ListCreateParticipantView,
    PlayerDetailView,
    PlayerListCreateView,
    RoomDetailView,
    RoomListCreate,
    StartGameHandOutView,
    end_game,
    start_game,
)

urlpatterns = [
    path("game/<int:pk>/settings/", DetailSettingsView.as_view(), name="game-settings"),
    path(
        "game_participants/",
        ListCreateParticipantView.as_view(),
        name="participants-list",
    ),
    path(
        "game_participants/<int:pk>",
        DetailParticipantView.as_view(),
        name="participant-detail",
    ),
    path("game/start/<uuid:room_id>/", start_game, name="start_game"),
    path("game/end/<int:game_id>/", end_game, name="end_game"),
    path("cards/get_six_cards/", StartGameHandOutView.as_view(), name="get_six_cards"),
    path("cards/get_one_card/", HandOutOneCardView.as_view(), name="get_one_card"),
    path("room/<int:pk>/", RoomDetailView.as_view(), name="room_detail"),
    path("rooms/", RoomListCreate.as_view(), name="room_list_create"),
    path("players/", PlayerListCreateView.as_view(), name="player_list_create"),
    path("player/<int:pk>/", PlayerDetailView.as_view(), name="player_detail"),
]
