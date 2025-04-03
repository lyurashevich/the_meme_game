from django.db import models
from game.models.card_models import SituationCard
from game.models.game_models import Game, GameParticipant


class GameRound(models.Model):
    """
    Represents a single round within a game session.

    - 'number': The number of the current round.
    - 'leader': The participant responsible for selecting the winner of this round.
                The leader should be assigned automatically in the order of participants joined the room.
    - 'situation_card': The card with the situation for this round.

    The 'save' method automatically assigns a round number based on the previous.
    """

    game = models.ForeignKey(Game, on_delete=models.CASCADE, related_name="rounds")
    number = models.PositiveIntegerField()
    leader = models.ForeignKey(GameParticipant, on_delete=models.CASCADE)
    situation_card = models.ForeignKey(SituationCard, on_delete=models.CASCADE)

    def save(self, *args, **kwargs) -> None:
        """
        Auto-assigns a round number.

        If it is the first round, the number is set to 1.
        """
        if not self.number:
            last_round = (
                GameRound.objects.filter(game=self.game).order_by("-number").first()
            )
            self.number = (last_round.number + 1) if last_round else 1
        super().save(*args, **kwargs)
