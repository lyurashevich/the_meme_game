from django.urls import path
from game.views import get_joke

from .views import (
    PostListCreateView,
    PostRetrieveUpdateDeleteView,
    get_test_image,
    health_check,
)

urlpatterns = [
    path("joke/", get_joke, name="joke"),
    path("tests/", PostListCreateView.as_view(), name="test-list-create"),
    path("test/<int:pk>/", PostRetrieveUpdateDeleteView.as_view(), name="test-detail"),
    path("test_image/", get_test_image, name="get_test_image"),
    path("healthcheck/", health_check, name="healthcheck"),
]
