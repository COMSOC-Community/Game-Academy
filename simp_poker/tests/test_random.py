from django.test import TestCase

from core.tests.helpers import make_session, make_user, make_player
from simp_poker.models import Answer
from simp_poker.random import create_random_answers
from simp_poker.tests.helpers import make_poker_game


class CreateRandomAnswersTests(TestCase):
    def setUp(self):
        self.session = make_session("sprandomsession")
        self.game = make_poker_game(self.session)
        self.players = [
            make_player(self.session, make_user(f"sprandomplayer{i}"))
            for i in range(3)
        ]

    def test_creates_one_answer_per_player(self):
        create_random_answers(self.game, self.players)
        self.assertEqual(Answer.objects.filter(game=self.game).count(), 3)

    def test_probabilities_are_within_zero_and_one(self):
        create_random_answers(self.game, self.players)
        for answer in Answer.objects.filter(game=self.game):
            for value in (
                answer.prob_p1_king, answer.prob_p1_queen, answer.prob_p1_jack,
                answer.prob_p2_king, answer.prob_p2_queen, answer.prob_p2_jack,
            ):
                self.assertGreaterEqual(value, 0)
                self.assertLessEqual(value, 1)

    def test_no_players_creates_no_answers(self):
        answers = create_random_answers(self.game, [])
        self.assertEqual(answers, [])
