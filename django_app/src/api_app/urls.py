from django.urls import path

from .views import PostListCreateView, PostRetrieveUpdateDeleteView

urlpatterns = [
    path("tests/", PostListCreateView.as_view(), name="test-list-create"),
    path("test/<int:pk>/", PostRetrieveUpdateDeleteView.as_view(), name="test-detail"),
]
