import random

from django.db.models import QuerySet
from game.models.card_models import Card, DiscardPile, PlayerCard
from game.serializers import CardSerializer, DiscardPileSerializer, PlayerCardSerializer
from rest_framework import status
from rest_framework.generics import GenericAPIView
from rest_framework.mixins import ListModelMixin
from rest_framework.request import Request
from rest_framework.response import Response


class StartGameHandOutView(GenericAPIView):
    """
    Hands out 6 random 'meme' cards at the beginning of the game.
    The cards are selected randomly from the pool of available 'meme' cards.
    """

    serializer_class = CardSerializer

    def get(self, request: Request) -> Response:
        cards = random.sample(list(Card.objects.filter(type="meme")), 6)
        return Response(CardSerializer(cards, many=True).data)


class HandOutOneCardView(GenericAPIView):
    """
    Gives one card, either 'meme' or 'situation', depending on the query parameter.
    Returns an error response if the card type is invalid.
    """

    serializer_class = CardSerializer

    def get(self, request: Request) -> Response:
        card_type = request.query_params.get("type")

        if card_type not in ["meme", "situation"]:
            return Response(
                {"error": "invalid card type"}, status=status.HTTP_400_BAD_REQUEST
            )
        cards = list(Card.objects.filter(type=card_type))
        card = random.choice(
            cards
        )  # nosec B311 - random is used only for game logic and doesn't affect security issues

        return Response(CardSerializer(card).data)


class PlayerCardsView(ListModelMixin, GenericAPIView):
    """
    Returns the 6 cards the participant has at the moment.
    The cards are filtered by the game ID and the participant ID.
    """

    queryset = PlayerCard
    serializer_class = PlayerCardSerializer
    lookup_field = "participant_id"

    def get_queryset(self) -> QuerySet[PlayerCard]:
        game_id = self.kwargs.get("game_id")
        participant_id = self.kwargs.get("participant_id")
        return PlayerCard.objects.filter(game_id=game_id, participant_id=participant_id)

    def get(self, request: Request, *args, **kwargs) -> Response:
        return self.list(request, *args, **kwargs)


class DiscardPileView(ListModelMixin, GenericAPIView):
    """
    Returns a list of discarded cards of the specific game.
    """

    queryset = DiscardPile
    serializer_class = DiscardPileSerializer

    def get_queryset(self) -> QuerySet[DiscardPile]:
        game_id = self.kwargs.get("game_id")
        return DiscardPile.objects.filter(game_id=game_id)

    def get(self, request: Request, *args, **kwargs) -> Response:
        return self.list(request, *args, **kwargs)
