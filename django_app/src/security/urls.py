from django.urls import path
from security.views import AnonymousTokenView

urlpatterns = [
    path("anonymous_token/", AnonymousTokenView.as_view(), name="anonymous_token"),
]
