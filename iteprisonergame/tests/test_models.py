from django.db import IntegrityError
from django.test import TestCase

from core.tests.helpers import make_session, make_user, make_player
from iteprisonergame.models import Setting, Answer, Score
from iteprisonergame.tests.helpers import make_itepris_game, ALWAYS_COOPERATE, TIT_FOR_TAT


class SettingModelTests(TestCase):
    def setUp(self):
        self.session = make_session("ipdsettingsession")
        self.game = make_itepris_game(self.session)

    def test_default_values(self):
        setting = Setting.objects.create(game=self.game)
        self.assertEqual(setting.num_repetitions, "168, 359, 306, 622, 319")
        self.assertTrue(setting.store_scores)
        self.assertEqual(setting.payoff_high, 0)
        self.assertEqual(setting.payoff_medium, -10)
        self.assertEqual(setting.payoff_low, -20)
        self.assertEqual(setting.payoff_tiny, -25)

    def test_one_to_one_with_game(self):
        setting = Setting.objects.create(game=self.game)
        self.assertEqual(self.game.itepris_setting, setting)


class AnswerModelTests(TestCase):
    def setUp(self):
        self.session = make_session("ipdanswersession")
        self.game = make_itepris_game(self.session)
        self.user = make_user("ipdanswerplayer")
        self.player = make_player(self.session, self.user)

    def make_answer(self, **overrides):
        data = dict(
            game=self.game, player=self.player, automata=ALWAYS_COOPERATE,
            initial_state="0", motivation="m", name="AC",
        )
        data.update(overrides)
        return Answer.objects.create(**data)

    def test_str(self):
        answer = self.make_answer(avg_score=1.5)
        self.assertIn(self.player.name, str(answer))
        self.assertNotIn("(win)", str(answer))

    def test_str_with_winner(self):
        answer = self.make_answer(winner=True)
        self.assertIn("(win)", str(answer))

    def test_unique_together_game_player(self):
        self.make_answer()
        with self.assertRaises(IntegrityError):
            self.make_answer()

    def test_formatted_avg_score_integer_valued(self):
        answer = self.make_answer(avg_score=5.0)
        self.assertEqual(answer.formatted_avg_score(), 5)
        self.assertIsInstance(answer.formatted_avg_score(), int)

    def test_formatted_avg_score_non_integer(self):
        answer = self.make_answer(avg_score=5.5)
        self.assertEqual(answer.formatted_avg_score(), 5.5)

    def test_number_states_single_line(self):
        answer = self.make_answer(automata=ALWAYS_COOPERATE)
        self.assertEqual(answer.number_states(), 1)

    def test_number_states_multi_line(self):
        answer = self.make_answer(automata=TIT_FOR_TAT)
        self.assertEqual(answer.number_states(), 2)


class ScoreModelTests(TestCase):
    def setUp(self):
        self.session = make_session("ipdscoresession")
        self.game = make_itepris_game(self.session)
        self.user1 = make_user("ipdscoreplayer1")
        self.user2 = make_user("ipdscoreplayer2")
        self.player1 = make_player(self.session, self.user1)
        self.player2 = make_player(self.session, self.user2)
        self.answer1 = Answer.objects.create(
            game=self.game, player=self.player1, automata=ALWAYS_COOPERATE,
            initial_state="0", motivation="m", name="A1",
        )
        self.answer2 = Answer.objects.create(
            game=self.game, player=self.player2, automata=ALWAYS_COOPERATE,
            initial_state="0", motivation="m", name="A2",
        )

    def test_str(self):
        score = Score.objects.create(
            answer=self.answer1, opponent=self.answer2, number_round=10,
            answer_avg_score=1.5, opp_avg_score=2.5,
        )
        self.assertIn(self.player1.name, str(score))
        self.assertIn(self.player2.name, str(score))

    def test_unique_together_answer_opponent_round(self):
        Score.objects.create(
            answer=self.answer1, opponent=self.answer2, number_round=10,
            answer_avg_score=1, opp_avg_score=2,
        )
        with self.assertRaises(IntegrityError):
            Score.objects.create(
                answer=self.answer1, opponent=self.answer2, number_round=10,
                answer_avg_score=3, opp_avg_score=4,
            )
