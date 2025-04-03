import random

from game.models.card_models import (
    DiscardPile,
    MemeCard,
    PlayerCard,
    SituationCard,
    UsedSituation,
)
from game.models.game_models import Game, GameParticipant
from game.models.game_round_models import GameRound


def get_available_cards():
    available_cards = MemeCard.objects.filter(
        playercard__isnull=True, discardpile__isnull=True
    )

    return available_cards


class GameManager:
    def __init__(self, game: Game):
        self.game = game
        self.participants = list(game.participants.all())
        self.score_limit = self.get_score_limit()
        self.score = {p.player: p.score for p in self.participants}
        self.current_round = self.get_current_round()

    def start_game(self):

        if len(self.participants) < 3:
            raise ValueError("you need at least 3 players to start game")

        self.hand_out_six_cards_to_players()

        situation_card = self.get_situation_card()

        self.current_round = GameRound.objects.create(
            game=self.game, leader=self.participants[0], situation_card=situation_card
        )

    def end_round(self, winner: GameParticipant, used_cards: list):

        card_ids = []

        for item in used_cards:
            if isinstance(item, PlayerCard):
                card_ids.append(item.card.id)
            elif isinstance(item, int):
                card_ids.append(item)
            else:
                ValueError("wrong type")

        PlayerCard.objects.filter(card_id__in=card_ids).delete()

        discards = [
            DiscardPile(
                card_id=card_id,
                round_expires=self.current_round.number + 20,
                game=self.game,
            )
            for card_id in card_ids
        ]

        DiscardPile.objects.bulk_create(discards)

        UsedSituation.objects.create(
            used_card=self.current_round.situation_card,
            round_expires=self.current_round.number + 30,
        )

        self.score[winner.player] += 1
        winner.score += 1
        winner.save()

        if self.score_limit and winner.score == self.score_limit:
            self.end_game()

        self.return_discarded_cards()

    def end_game(self):

        if self.game.participants.exists():
            self.game.participants.all().delete()

        if self.game.rounds.exists():
            self.game.rounds.all().delete()

        self.game.delete()

    def start_new_round(self):

        if not self.participants:
            raise ValueError("no players in game")

        self.hand_out_one_card_to_player(self.current_round.leader)

        new_leader = self.select_new_leader()

        new_situation_card = GameManager.get_situation_card()

        self.current_round = GameRound.objects.create(
            game=self.game, leader=new_leader, situation_card=new_situation_card
        )

    def get_score_limit(self):

        settings = self.game.gamesettings_set.first()

        if not settings:
            return None
        return None if settings.score_limit == 0 else settings.score_limit

    def get_current_round(self):
        return self.game.rounds.order_by("-number").first()

    def select_new_leader(self):

        last_leader_index = self.participants.index(self.current_round.leader)
        new_leader_index = (last_leader_index + 1) % len(self.participants)

        return self.participants[new_leader_index]

    def hand_out_six_cards_to_players(self):

        available_cards = list(get_available_cards())
        random.shuffle(available_cards)

        if len(available_cards) < 6 * len(self.participants):
            raise ValueError("not enough cards in the deck")

        cards_to_create = []
        card_index = 0

        for participant in self.participants:
            meme_cards = available_cards[
                card_index : card_index + 6  # noqa: E203 (for flake8)
            ]
            card_index += 6

            for card in meme_cards:
                cards_to_create.append(
                    PlayerCard(participant=participant, card=card, game=self.game)
                )

        PlayerCard.objects.bulk_create(cards_to_create)

    def hand_out_one_card_to_player(self, leader: GameParticipant):

        available_cards = list(get_available_cards())
        random.shuffle(available_cards)

        players_needing_cards = [
            p for p in self.participants if p != self.current_round.leader
        ]

        if len(available_cards) < len(players_needing_cards):
            raise ValueError("not enough cards in the deck")

        cards_to_create = []

        for participant in players_needing_cards:
            card = available_cards.pop()
            cards_to_create.append(
                PlayerCard(participant=participant, card=card, game=self.game)
            )

        PlayerCard.objects.bulk_create(cards_to_create)

    @staticmethod
    def get_situation_card():

        used_situations = UsedSituation.objects.values_list("used_card_id", flat=True)
        available_situations = SituationCard.objects.exclude(id__in=used_situations)

        return available_situations.order_by("?").first()

    def return_discarded_cards(self):

        current_round_number = self.current_round.number

        old_cards = DiscardPile.objects.filter(round_expires__lte=current_round_number)
        old_situations = UsedSituation.objects.filter(
            round_expires__lte=current_round_number
        )

        old_cards.delete()
        old_situations.delete()
