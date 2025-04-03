from django.urls import path
from game.views.game_views import (
    DetailSettingsView,
    GameDetailView,
    GameListCreate,
    start_game,
)
from game.views.player_views import PlayerDetailView, PlayerListCreateView

urlpatterns = [
    path("games/", GameListCreate.as_view(), name="game-list-create"),
    path("games/<int:pk>/", GameDetailView.as_view(), name="game-detail-view"),
    path("games/<int:game_id>/start_game/", start_game, name="start-game"),
    path(
        "games/<int:game_id>/settings/",
        DetailSettingsView.as_view(),
        name="game-settings",
    ),
    path("players/", PlayerListCreateView.as_view(), name="player_list_create"),
    path("player/<int:pk>/", PlayerDetailView.as_view(), name="player_detail"),
]
