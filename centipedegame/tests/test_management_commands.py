import io

from django.core.management import call_command
from django.test import TestCase, SimpleTestCase

from core.tests.helpers import make_session, make_user, make_player
from centipedegame.management.commands.centi_computescores import payoffs
from centipedegame.models import Answer, Result, Setting
from centipedegame.tests.helpers import make_centipede_game


class _FakeGame:
    def __init__(self, setting):
        self.centi_setting = setting


class _FakeAnswer:
    def __init__(self, strategy_as_p1, strategy_as_p2):
        self.strategy_as_p1 = strategy_as_p1
        self.strategy_as_p2 = strategy_as_p2


class PayoffsTests(TestCase):
    def setUp(self):
        self.session = make_session("centipayoffsession")
        self.game = make_centipede_game(self.session)
        self.setting = Setting.objects.create(
            game=self.game,
            payoff_d_p1=1, payoff_d_p2=2,
            payoff_rd_p1=3, payoff_rd_p2=4,
            payoff_rrd_p1=5, payoff_rrd_p2=6,
            payoff_rrrd_p1=7, payoff_rrrd_p2=8,
            payoff_rrrr_p1=9, payoff_rrrr_p2=10,
        )

    def test_d_outcome_when_p1_stops_immediately(self):
        p1 = _FakeAnswer("Down - Down", "Right - Right")
        p2 = _FakeAnswer("Right - Right", "Right - Right")
        self.assertEqual(payoffs(self.game, p1, p2), (1, 2))

    def test_rd_outcome_when_p2_stops_at_first_opportunity(self):
        p1 = _FakeAnswer("Right - Right", "Right - Right")
        p2 = _FakeAnswer("Right - Right", "Down - Down")
        self.assertEqual(payoffs(self.game, p1, p2), (3, 4))

    def test_rrd_outcome_when_p1_stops_at_second_opportunity(self):
        p1 = _FakeAnswer("Right - Down", "Right - Right")
        p2 = _FakeAnswer("Right - Right", "Right - Right")
        self.assertEqual(payoffs(self.game, p1, p2), (5, 6))

    def test_rrrd_outcome_when_p2_stops_at_second_opportunity(self):
        p1 = _FakeAnswer("Right - Right", "Right - Right")
        p2 = _FakeAnswer("Right - Right", "Right - Down")
        self.assertEqual(payoffs(self.game, p1, p2), (7, 8))

    def test_rrrr_outcome_when_neither_stops(self):
        p1 = _FakeAnswer("Right - Right", "Right - Right")
        p2 = _FakeAnswer("Right - Right", "Right - Right")
        self.assertEqual(payoffs(self.game, p1, p2), (9, 10))


class CentiComputeScoresCommandTests(TestCase):
    def setUp(self):
        self.session = make_session("centicmdsession")
        self.game = make_centipede_game(self.session)
        self.setting = Setting.objects.create(game=self.game)

    def run_command(self, **kwargs):
        stderr = io.StringIO()
        stdout = io.StringIO()
        call_command("centi_computescores", stderr=stderr, stdout=stdout, **kwargs)
        return stdout.getvalue(), stderr.getvalue()

    def make_answer(self, name, strategy_as_p1, strategy_as_p2, **overrides):
        user = make_user(name)
        player = make_player(self.session, user, name=name)
        data = dict(
            game=self.game, player=player,
            strategy_as_p1=strategy_as_p1, strategy_as_p2=strategy_as_p2, motivation="m",
        )
        data.update(overrides)
        return Answer.objects.create(**data)

    def test_missing_session_argument_reports_error(self):
        _, stderr = self.run_command(session="", game=self.game.url_tag)
        self.assertIn("session", stderr)

    def test_unknown_session_reports_error(self):
        _, stderr = self.run_command(session="doesnotexist", game=self.game.url_tag)
        self.assertIn("no session", stderr)

    def test_missing_game_argument_reports_error(self):
        _, stderr = self.run_command(session=self.session.url_tag, game="")
        self.assertIn("game", stderr)

    def test_unknown_game_reports_error(self):
        _, stderr = self.run_command(session=self.session.url_tag, game="doesnotexist")
        self.assertIn("no game", stderr)

    def test_no_answers_still_creates_empty_result(self):
        self.run_command(session=self.session.url_tag, game=self.game.url_tag)
        self.game.refresh_from_db()
        self.assertIsNotNone(self.game.result_centi)

    def test_single_answer_scores_zero_and_wins_by_default(self):
        answer = self.make_answer("centicmdsolo", "Right - Right", "Right - Right")
        self.run_command(session=self.session.url_tag, game=self.game.url_tag)
        answer.refresh_from_db()
        self.assertEqual(answer.avg_score, 0)
        self.assertTrue(answer.winning)

    def test_each_players_own_p1_and_p2_payoffs_are_correctly_attributed(self):
        self.setting.payoff_d_p1 = 1
        self.setting.payoff_d_p2 = 2
        self.setting.payoff_rrrr_p1 = 3
        self.setting.payoff_rrrr_p2 = 100
        self.setting.save()
        # X always stops immediately as p1, and never stops early as p2.
        x = self.make_answer("centicmdx", "Down - Down", "Right - Right")
        # Y never stops early as p1, and always stops immediately as p2.
        y = self.make_answer("centicmdy", "Right - Right", "Down - Down")
        self.run_command(session=self.session.url_tag, game=self.game.url_tag)
        x.refresh_from_db()
        y.refresh_from_db()

        # X as p1 vs Y as p2: X stops immediately (D outcome) -> X earns payoff_d_p1 = 1.
        self.assertEqual(x.avg_score_as_p1, 1)
        # Y as p1 vs X as p2: neither stops (RRRR outcome) -> X (as p2) earns payoff_rrrr_p2 = 100.
        self.assertEqual(x.avg_score_as_p2, 100)

        # Y as p1 vs X as p2: RRRR outcome -> Y (as p1) earns payoff_rrrr_p1 = 3.
        self.assertEqual(y.avg_score_as_p1, 3)
        # X as p1 vs Y as p2: D outcome -> Y (as p2) earns payoff_d_p2 = 2.
        self.assertEqual(y.avg_score_as_p2, 2)

        self.assertTrue(x.winning)
        self.assertFalse(y.winning)

    def test_tied_best_score_produces_multiple_winners(self):
        a = self.make_answer("centicmdtie1", "Right - Right", "Right - Right")
        b = self.make_answer("centicmdtie2", "Right - Right", "Right - Right")
        self.run_command(session=self.session.url_tag, game=self.game.url_tag)
        a.refresh_from_db()
        b.refresh_from_db()
        self.assertTrue(a.winning)
        self.assertTrue(b.winning)

    def test_histogram_and_heatmap_data_populated(self):
        self.make_answer("centicmdp1", "Down - Down", "Right - Right")
        self.make_answer("centicmdp2", "Right - Right", "Down - Down")
        self.run_command(session=self.session.url_tag, game=self.game.url_tag)
        self.game.refresh_from_db()
        self.assertIn("Down - Down", self.game.result_centi.histo_strat1_js_data)
        self.assertIn("Down - Down", self.game.result_centi.histo_strat2_js_data)
        self.assertNotEqual(self.game.result_centi.scores_heatmap_js_data, "")

    def test_rerun_does_not_duplicate_result(self):
        self.make_answer("centicmdp3", "Right - Right", "Right - Right")
        self.run_command(session=self.session.url_tag, game=self.game.url_tag)
        self.make_answer("centicmdp4", "Down - Down", "Down - Down")
        self.run_command(session=self.session.url_tag, game=self.game.url_tag)
        self.assertEqual(Result.objects.filter(game=self.game).count(), 1)
