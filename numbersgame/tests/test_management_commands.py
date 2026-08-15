import io

from django.core.management import call_command
from django.test import TestCase

from core.tests.helpers import make_session, make_user, make_game, make_player
from numbersgame.models import Answer, Result, Setting


class NumbersgameResultsCommandTests(TestCase):
    def setUp(self):
        self.session = make_session("ngcmdsession")
        self.game = make_game(self.session, url_tag="numb")
        Setting.objects.create(
            game=self.game, lower_bound=0, upper_bound=100, factor=1, histogram_bin_size=10,
        )

    def run_command(self, **kwargs):
        stderr = io.StringIO()
        stdout = io.StringIO()
        call_command(
            "numbersgame_results", stderr=stderr, stdout=stdout, **kwargs
        )
        return stdout.getvalue(), stderr.getvalue()

    def make_answer(self, name, value):
        user = make_user(name)
        player = make_player(self.session, user, name=name)
        return Answer.objects.create(game=self.game, player=player, answer=value, motivation="m")

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
        stdout, stderr = self.run_command(session=self.session.url_tag, game=self.game.url_tag)
        self.assertEqual(stderr, "")
        self.game.refresh_from_db()
        self.assertIsNotNone(self.game.result_ng)
        self.assertIsNone(self.game.result_ng.average)

    def test_computes_average_and_corrected_average(self):
        self.make_answer("ngcmdp1", 0)
        self.make_answer("ngcmdp2", 100)
        self.run_command(session=self.session.url_tag, game=self.game.url_tag)
        self.game.refresh_from_db()
        self.assertEqual(self.game.result_ng.average, 50)
        self.assertEqual(self.game.result_ng.corrected_average, 50)

    def test_single_winner_is_closest_to_corrected_average(self):
        a1 = self.make_answer("ngcmdp3", 40)
        a2 = self.make_answer("ngcmdp4", 60)
        self.run_command(session=self.session.url_tag, game=self.game.url_tag)
        a1.refresh_from_db()
        a2.refresh_from_db()
        # average = 50, corrected_average = 50 (factor=1); both are equidistant -> tie
        self.assertTrue(a1.winner)
        self.assertTrue(a2.winner)

    def test_clear_single_winner(self):
        # average = 40, corrected_average = 40 (factor=1); gaps are 30, 20, 50 respectively,
        # so ngcmdp5b is the unambiguous single winner.
        loser1 = self.make_answer("ngcmdp5a", 10)
        winner = self.make_answer("ngcmdp5b", 20)
        loser2 = self.make_answer("ngcmdp5c", 90)
        self.run_command(session=self.session.url_tag, game=self.game.url_tag)
        loser1.refresh_from_db()
        winner.refresh_from_db()
        loser2.refresh_from_db()
        self.assertTrue(winner.winner)
        self.assertFalse(loser1.winner)
        self.assertFalse(loser2.winner)

    def test_gap_is_stored_on_each_answer(self):
        # Single answer: average == corrected_average == the answer itself, so gap is 0.
        answer = self.make_answer("ngcmdp7", 30)
        self.run_command(session=self.session.url_tag, game=self.game.url_tag)
        answer.refresh_from_db()
        self.assertEqual(answer.gap, 0)

    def test_rerun_replaces_previous_result(self):
        self.make_answer("ngcmdp8", 20)
        self.run_command(session=self.session.url_tag, game=self.game.url_tag)
        first_result_id = self.game.result_ng.id
        self.make_answer("ngcmdp9", 80)
        self.run_command(session=self.session.url_tag, game=self.game.url_tag)
        self.game.refresh_from_db()
        self.assertNotEqual(self.game.result_ng.id, first_result_id)
        self.assertEqual(Result.objects.filter(game=self.game).count(), 1)

    def test_histogram_data_is_populated(self):
        self.make_answer("ngcmdp10", 15)
        self.run_command(session=self.session.url_tag, game=self.game.url_tag)
        self.game.refresh_from_db()
        self.assertIn("10", self.game.result_ng.histo_js_data)
