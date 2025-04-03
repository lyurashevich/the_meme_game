import pytest
from django.core.exceptions import ObjectDoesNotExist
from django.test import TestCase
from game.models.card_models import (
    DiscardPile,
    MemeCard,
    PlayerCard,
    SituationCard,
    UsedSituation,
)
from game.models.game_models import (
    Game,
    GameParticipant,
    GameSettings,
    TooManyPlayersError,
)
from game.models.game_round_models import GameRound
from game.models.player_models import Player


class TestGameManager(TestCase):

    def setUp(self):
        from game.game_logic import GameManager

        self.owner = Player.objects.create_user()
        self.game = Game.objects.create(owner=self.owner)
        self.player1 = Player.objects.create_user()
        self.game.add_player(self.player1)

        self.player2 = Player.objects.create_user()
        self.game.add_player(self.player2)

        self.meme_cards = [
            MemeCard.objects.create(image_url=f"http://example.com/meme{i}")
            for i in range(25)
        ]
        self.situation_cards = [
            SituationCard.objects.create(text=f"situation {i}") for i in range(5)
        ]

        self.manager = GameManager(self.game)

    def test_add_players(self):
        self.assertEqual(self.game.participants.count(), 3)

        player3 = Player.objects.create_user()
        self.game.add_player(player3)
        self.assertEqual(self.game.participants.count(), 4)

    def test_start_game(self):
        self.manager.start_game()
        self.assertEqual(self.game.rounds.count(), 1)
        self.assertEqual(self.manager.current_round.number, 1)
        self.assertEqual(self.manager.score_limit, None)

        self.assertIsNotNone(self.manager.current_round.situation_card)
        self.assertEqual(
            list(self.game.participants.all())[0].playercard_set.count(), 6
        )
        self.assertEqual(
            list(self.game.participants.all())[1].playercard_set.count(), 6
        )
        self.assertEqual(
            list(self.game.participants.all())[2].playercard_set.count(), 6
        )
        self.assertEqual(list(self.game.participants.all())[0].player, self.owner)
        self.assertEqual(PlayerCard.objects.all().count(), 18)

    def test_end_round(self):
        self.manager.start_game()
        participants = list(self.game.participants.all())
        winner = participants[1]

        self.assertEqual(self.manager.current_round.number, 1)

        other_players = [
            player
            for player in participants
            if player != self.manager.current_round.leader
        ]
        used_cards = [player.playercard_set.first() for player in other_players]
        used_card_ids = [card.card.id for card in used_cards]

        self.assertEqual(len(used_card_ids), 2)
        self.manager.end_round(winner, used_cards)

        self.assertEqual(participants[0].playercard_set.count(), 6)
        self.assertEqual(participants[1].playercard_set.count(), 5)
        self.assertEqual(participants[2].playercard_set.count(), 5)

    def test_score_after_round(self):
        self.manager.start_game()
        participants = list(self.game.participants.all())

        for p in participants:
            self.assertEqual(self.manager.score[p.player], 0)
            self.assertEqual(p.score, 0)

        winner = participants[1]
        other_players = [
            player
            for player in participants
            if player != self.manager.current_round.leader
        ]
        used_cards = [player.playercard_set.first() for player in other_players]
        used_card_ids = [card.card.id for card in used_cards]

        self.manager.end_round(winner, used_card_ids)

        for i, p in enumerate(participants):
            if p == winner:
                self.assertEqual(self.manager.score[p.player], 1)
                self.assertEqual(p.score, 1)
            else:
                self.assertEqual(self.manager.score[p.player], 0)
                self.assertEqual(p.score, 0)

    def test_start_new_round(self):
        self.manager.start_game()
        participants = list(self.game.participants.all())
        winner = participants[2]
        other_players = [
            player
            for player in participants
            if player != self.manager.current_round.leader
        ]
        used_cards = [player.playercard_set.first() for player in other_players]
        used_card_ids = [card.card.id for card in used_cards]
        self.manager.end_round(winner, used_card_ids)
        self.manager.start_new_round()

        self.assertEqual(self.manager.current_round.number, 2)
        self.assertEqual(self.manager.current_round.leader, participants[1])

        self.assertEqual(DiscardPile.objects.all().count(), 2)
        self.assertEqual(UsedSituation.objects.all().count(), 1)
        self.assertEqual(PlayerCard.objects.all().count(), 18)

        self.assertEqual(participants[0].playercard_set.count(), 6)
        self.assertEqual(participants[1].playercard_set.count(), 6)
        self.assertEqual(participants[2].playercard_set.count(), 6)

    def test_discard_pile_creation(self):
        self.manager.start_game()
        participants = list(self.game.participants.all())
        winner = participants[2]
        other_players = [
            player
            for player in participants
            if player != self.manager.current_round.leader
        ]
        used_cards = [player.playercard_set.first() for player in other_players]
        used_card_ids = [card.card.id for card in used_cards]
        self.manager.end_round(winner, used_card_ids)

        for card_id in used_card_ids:
            self.assertTrue(DiscardPile.objects.filter(card_id=card_id).exists())

    def test_end_game(self):
        self.manager.start_game()

        self.assertTrue(self.game.rounds.exists())
        self.assertTrue(self.game.participants.exists())

        self.manager.end_game()

        with pytest.raises(ObjectDoesNotExist):
            Game.objects.get(id=self.game.id)
            GameParticipant.objects.get(game=self.game)
            GameRound.objects.get(game=self.game)

    def test_not_enough_cards(self):
        MemeCard.objects.all().delete()
        [
            MemeCard.objects.create(image_url=f"http://example.com/meme{i}")
            for i in range(5)
        ]

        with self.assertRaises(ValueError) as detail:
            self.manager.start_game()
        self.assertIn("not enough cards", str(detail.exception))

    def test_if_cards_unique(self):
        self.manager.start_game()
        all_cards = list(PlayerCard.objects.values_list("card_id", flat=True))
        self.assertEqual(len(all_cards), len(set(all_cards)))

    def test_leader_rotation(self):
        self.manager.start_game()
        initial_leader = self.manager.current_round.leader

        winner = list(self.game.participants.all())[1]
        self.manager.end_round(winner, [])
        self.manager.start_new_round()

        new_leader = self.manager.current_round.leader
        self.assertNotEqual(initial_leader, new_leader)

    def test_max_players_validation(self):
        player1 = Player.objects.create()
        game = Game.objects.create(owner=player1, max_players=2)

        player2 = Player.objects.create()

        game.add_player(player2)
        assert game.participants.count() == 2

        player3 = Player.objects.create_user()
        with pytest.raises(TooManyPlayersError):
            game.add_player(player3)

        with pytest.raises(TooManyPlayersError):
            game.add_player(player2)

        assert game.participants.count() == 2

    def test_start_game_with_one_player(self):
        from game.game_logic import GameManager

        player1 = Player.objects.create_user()
        game = Game.objects.create(owner=player1)
        manager = GameManager(game)

        with pytest.raises(ValueError):
            manager.start_game()

    def test_game_with_score_limit(self):
        from game.game_logic import GameManager

        player1 = Player.objects.create_user()
        player2 = Player.objects.create_user()
        player3 = Player.objects.create_user()
        game = Game.objects.create(owner=player1)
        game.add_player(player3)
        game.add_player(player2)
        GameSettings.objects.create(game=game, score_limit=1)
        manager = GameManager(game)

        self.assertEqual(manager.get_score_limit(), 1)

        manager.start_game()
        winner = list(game.participants.all())[1]
        manager.end_round(winner, [])

        with pytest.raises(ObjectDoesNotExist):
            Game.objects.get(id=game.id)

    def test_return_discarded_cards(self):
        from game.game_logic import get_available_cards

        self.manager.start_game()

        available_cards = get_available_cards()

        winner = list(self.game.participants.all())[1]
        card_id = winner.playercard_set.first().card_id
        self.manager.end_round(winner, [card_id])

        self.manager.current_round.number = 19
        self.manager.current_round.save()
        self.manager.return_discarded_cards()
        self.assertTrue(DiscardPile.objects.filter(card_id=card_id).exists())
        self.assertNotIn(card_id, available_cards.values_list("id", flat=True))

        self.assertTrue(DiscardPile.objects.filter(card_id=card_id).exists())
        self.manager.current_round.number = 23
        self.manager.current_round.save()
        self.manager.return_discarded_cards()

        self.assertFalse(DiscardPile.objects.filter(card_id=card_id).exists())
        self.assertIn(card_id, available_cards.values_list("id", flat=True))

    def test_return_discarded_situation_card(self):
        self.manager.start_game()
        situation_card_id = self.manager.current_round.situation_card.id

        winner = list(self.game.participants.all())[1]
        card_id = winner.playercard_set.first().card_id
        self.manager.end_round(winner, [card_id])

        self.assertTrue(
            UsedSituation.objects.filter(used_card=situation_card_id).exists()
        )

        self.manager.current_round.number = 32
        self.manager.current_round.save()
        self.manager.return_discarded_cards()
        self.assertFalse(
            UsedSituation.objects.filter(used_card=situation_card_id).exists()
        )
