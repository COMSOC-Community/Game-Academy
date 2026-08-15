from django.db import IntegrityError
from django.test import TestCase

from core.tests.helpers import make_session, make_user, make_player
from simp_poker.models import Answer, Result
from simp_poker.tests.helpers import make_poker_game


class AnswerModelTests(TestCase):
    def setUp(self):
        self.session = make_session("spanswersession")
        self.game = make_poker_game(self.session)
        self.user = make_user("spanswerplayer")
        self.player = make_player(self.session, self.user)

    def make_answer(self, **overrides):
        data = dict(
            game=self.game, player=self.player,
            prob_p1_king=1, prob_p1_queen=0.5, prob_p1_jack=0.25,
            prob_p2_king=1, prob_p2_queen=0.5, prob_p2_jack=0,
            motivation="m",
        )
        data.update(overrides)
        return Answer.objects.create(**data)

    def test_str(self):
        answer = self.make_answer()
        self.assertIn(self.player.name, str(answer))
        self.assertIn(self.game.name, str(answer))

    def test_unique_together_game_player(self):
        self.make_answer()
        with self.assertRaises(IntegrityError):
            self.make_answer()

    def test_probabilities_as_tuple_formats_all_six_values(self):
        answer = self.make_answer()
        formatted = answer.probabilities_as_tuple
        self.assertEqual(formatted, "1, 0.5, 0.25, 1, 0.5, 0")

    def test_best_response_as_answer_none_when_not_set(self):
        answer = self.make_answer()
        self.assertIsNone(answer.best_response_as_answer)

    def test_best_response_as_answer_parses_csv_string(self):
        answer = self.make_answer(best_response="1,1,0,1,1,0")
        derived = answer.best_response_as_answer
        self.assertEqual(derived.prob_p1_king, 1)
        self.assertEqual(derived.prob_p1_queen, 1)
        self.assertEqual(derived.prob_p1_jack, 0)
        self.assertEqual(derived.prob_p2_king, 1)
        self.assertEqual(derived.prob_p2_queen, 1)
        self.assertEqual(derived.prob_p2_jack, 0)
        self.assertEqual(derived.game, self.game)
        self.assertEqual(derived.player, self.player)


class ResultModelTests(TestCase):
    def setUp(self):
        self.session = make_session("spresultsession")
        self.game = make_poker_game(self.session)

    def test_one_to_one_with_game(self):
        result = Result.objects.create(game=self.game)
        self.assertEqual(self.game.simp_poker_res, result)

    def test_str(self):
        result = Result.objects.create(game=self.game)
        self.assertEqual(str(result), f"{self.game.name} - Results Data")

    def test_global_best_response_as_answer_parses_csv_string(self):
        user = make_user("spresultplayer")
        make_player(self.session, user)
        result = Result.objects.create(
            game=self.game, global_best_response="1,1,0.5,1,0.25,0"
        )
        derived = result.global_best_response_as_answer()
        self.assertEqual(derived.prob_p1_king, 1)
        self.assertEqual(derived.prob_p1_jack, 0.5)
        self.assertEqual(derived.prob_p2_queen, 0.25)
        self.assertEqual(derived.game, self.game)
