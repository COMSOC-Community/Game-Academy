from django.test import TestCase

from core.tests.helpers import make_session, make_user, make_player
from auctiongame.models import Answer, Setting
from auctiongame.random import create_random_answers
from auctiongame.tests.helpers import make_auction_game


class CreateRandomAnswersTests(TestCase):
    def setUp(self):
        self.session = make_session("auctrandomsession")
        self.game = make_auction_game(self.session)
        Setting.objects.create(game=self.game, number_auctions=3, valuation_sampler="constant")
        self.players = [
            make_player(self.session, make_user(f"auctrandomplayer{i}"))
            for i in range(3)
        ]

    def test_creates_one_answer_per_player(self):
        create_random_answers(self.game, self.players)
        self.assertEqual(Answer.objects.filter(game=self.game).count(), 3)

    def test_auction_id_within_configured_range(self):
        create_random_answers(self.game, self.players)
        for answer in Answer.objects.filter(game=self.game):
            self.assertGreaterEqual(answer.auction_id, 1)
            self.assertLessEqual(answer.auction_id, 3)

    def test_valuation_matches_constant_sampler(self):
        create_random_answers(self.game, self.players)
        for answer in Answer.objects.filter(game=self.game):
            self.assertEqual(answer.valuation, 10 + answer.auction_id)

    def test_bid_is_within_three_below_valuation(self):
        create_random_answers(self.game, self.players)
        for answer in Answer.objects.filter(game=self.game):
            bid = float(answer.bid)
            self.assertGreaterEqual(bid, answer.valuation - 3)
            self.assertLessEqual(bid, answer.valuation)

    def test_no_players_creates_no_answers(self):
        answers = create_random_answers(self.game, [])
        self.assertEqual(answers, [])
