from django.test import TestCase

from core.tests.helpers import make_session, make_user, make_player
from centipedegame.constants import CENTIPEDE_STRATEGIES
from centipedegame.models import Answer
from centipedegame.random import create_random_answers
from centipedegame.tests.helpers import make_centipede_game


class CreateRandomAnswersTests(TestCase):
    def setUp(self):
        self.session = make_session("centirandomsession")
        self.game = make_centipede_game(self.session)
        self.players = [
            make_player(self.session, make_user(f"centirandomplayer{i}"))
            for i in range(3)
        ]

    def test_creates_one_answer_per_player(self):
        create_random_answers(self.game, self.players)
        self.assertEqual(Answer.objects.filter(game=self.game).count(), 3)

    def test_strategies_are_valid_choices(self):
        create_random_answers(self.game, self.players)
        for answer in Answer.objects.filter(game=self.game):
            self.assertIn(answer.strategy_as_p1, CENTIPEDE_STRATEGIES)
            self.assertIn(answer.strategy_as_p2, CENTIPEDE_STRATEGIES)

    def test_no_players_creates_no_answers(self):
        answers = create_random_answers(self.game, [])
        self.assertEqual(answers, [])
