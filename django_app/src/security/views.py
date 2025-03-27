from datetime import timedelta

from rest_framework.response import Response
from rest_framework.views import APIView
from rest_framework_simplejwt.tokens import AccessToken


class AnonymousTokenView(APIView):
    def post(self, request):
        token = AccessToken()
        token.set_exp(from_time=None, lifetime=timedelta(minutes=15))
        return Response({"access": str(token)})
