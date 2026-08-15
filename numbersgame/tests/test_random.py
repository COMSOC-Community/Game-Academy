from django.test import TestCase

from core.tests.helpers import make_session, make_user, make_game, make_player
from numbersgame.models import Answer, Setting
from numbersgame.random import create_random_answers


class CreateRandomAnswersTests(TestCase):
    def setUp(self):
        self.session = make_session("ngrandomanswersession")
        self.game = make_game(self.session, url_tag="numb")
        Setting.objects.create(game=self.game, lower_bound=10, upper_bound=20)
        self.players = [
            make_player(self.session, make_user(f"ngrandomplayer{i}"))
            for i in range(3)
        ]

    def test_creates_one_answer_per_player(self):
        answers = create_random_answers(self.game, self.players)
        self.assertEqual(len(answers), 3)
        self.assertEqual(Answer.objects.filter(game=self.game).count(), 3)

    def test_answers_are_within_bounds(self):
        create_random_answers(self.game, self.players)
        for answer in Answer.objects.filter(game=self.game):
            self.assertGreaterEqual(answer.answer, 10)
            self.assertLessEqual(answer.answer, 20)

    def test_answers_have_motivation_text(self):
        answers = create_random_answers(self.game, self.players)
        for answer in answers:
            self.assertEqual(answer.motivation, "Answer has been randomly generated")

    def test_no_players_creates_no_answers(self):
        answers = create_random_answers(self.game, [])
        self.assertEqual(answers, [])
