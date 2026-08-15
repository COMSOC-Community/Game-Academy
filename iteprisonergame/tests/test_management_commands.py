import io

from django.core.management import call_command
from django.test import TestCase

from core.tests.helpers import make_session, make_user, make_player
from iteprisonergame.models import Answer, Score, Setting
from iteprisonergame.tests.helpers import make_itepris_game, ALWAYS_COOPERATE, ALWAYS_DEFECT


class IpdComputeResultsCommandTests(TestCase):
    def setUp(self):
        self.session = make_session("ipdcomputecmdsession")
        self.game = make_itepris_game(self.session)
        self.setting = Setting.objects.create(
            game=self.game, num_repetitions="10",
            payoff_high=5, payoff_medium=3, payoff_low=1, payoff_tiny=2,
        )

    def run_command(self, **kwargs):
        stderr = io.StringIO()
        stdout = io.StringIO()
        call_command("ipd_computeresults", stderr=stderr, stdout=stdout, **kwargs)
        return stdout.getvalue(), stderr.getvalue()

    def make_answer(self, name, automata, **overrides):
        user = make_user(name)
        player = make_player(self.session, user, name=name)
        data = dict(
            game=self.game, player=player, automata=automata, initial_state="0",
            motivation="m", name=name,
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

    def test_mutual_cooperation_scores_the_medium_payoff_each_round(self):
        a = self.make_answer("ipdcmdcoop1", ALWAYS_COOPERATE)
        b = self.make_answer("ipdcmdcoop2", ALWAYS_COOPERATE)
        self.run_command(session=self.session.url_tag, game=self.game.url_tag)
        a.refresh_from_db()
        b.refresh_from_db()
        self.assertEqual(a.avg_score, 3)
        self.assertEqual(b.avg_score, 3)
        self.assertTrue(a.winner)
        self.assertTrue(b.winner)

    def test_defector_beats_cooperator(self):
        defector = self.make_answer("ipdcmddefect", ALWAYS_DEFECT)
        cooperator = self.make_answer("ipdcmdcoop", ALWAYS_COOPERATE)
        self.run_command(session=self.session.url_tag, game=self.game.url_tag)
        defector.refresh_from_db()
        cooperator.refresh_from_db()
        self.assertEqual(defector.avg_score, 5)
        self.assertEqual(cooperator.avg_score, 1)
        self.assertTrue(defector.winner)
        self.assertFalse(cooperator.winner)

    def test_pairwise_scores_are_stored_when_enabled(self):
        self.make_answer("ipdcmdstorea", ALWAYS_COOPERATE)
        self.make_answer("ipdcmdstoreb", ALWAYS_DEFECT)
        self.run_command(session=self.session.url_tag, game=self.game.url_tag)
        self.assertTrue(Score.objects.filter(answer__game=self.game).exists())

    def test_pairwise_scores_are_skipped_when_disabled(self):
        self.setting.store_scores = False
        self.setting.save()
        self.make_answer("ipdcmdnostorea", ALWAYS_COOPERATE)
        self.make_answer("ipdcmdnostoreb", ALWAYS_DEFECT)
        self.run_command(session=self.session.url_tag, game=self.game.url_tag)
        self.assertFalse(Score.objects.filter(answer__game=self.game).exists())

    def test_multiple_repetition_lengths_are_all_played(self):
        self.setting.num_repetitions = "5,10"
        self.setting.save()
        self.make_answer("ipdcmdmultia", ALWAYS_COOPERATE)
        self.make_answer("ipdcmdmultib", ALWAYS_COOPERATE)
        self.run_command(session=self.session.url_tag, game=self.game.url_tag)
        rounds_played = set(
            Score.objects.filter(answer__game=self.game).values_list(
                "number_round", flat=True
            )
        )
        self.assertEqual(rounds_played, {5, 10})

    def test_rerun_clears_previous_scores(self):
        self.make_answer("ipdcmdreruna", ALWAYS_COOPERATE)
        self.make_answer("ipdcmdrerunb", ALWAYS_DEFECT)
        self.run_command(session=self.session.url_tag, game=self.game.url_tag)
        first_count = Score.objects.filter(answer__game=self.game).count()
        self.run_command(session=self.session.url_tag, game=self.game.url_tag)
        second_count = Score.objects.filter(answer__game=self.game).count()
        self.assertEqual(first_count, second_count)


class IpdGenerateGraphDataCommandTests(TestCase):
    def setUp(self):
        self.session = make_session("ipdgraphcmdsession")
        self.game = make_itepris_game(self.session)
        self.user = make_user("ipdgraphplayer")
        self.player = make_player(self.session, self.user)

    def run_command(self, **kwargs):
        stderr = io.StringIO()
        stdout = io.StringIO()
        call_command("ipd_generategraphdata", stderr=stderr, stdout=stdout, **kwargs)
        return stdout.getvalue(), stderr.getvalue()

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

    def test_populates_graph_json_data(self):
        answer = Answer.objects.create(
            game=self.game, player=self.player, automata=ALWAYS_COOPERATE,
            initial_state="0", motivation="m", name="AC",
        )
        self.run_command(session=self.session.url_tag, game=self.game.url_tag)
        answer.refresh_from_db()
        self.assertIsNotNone(answer.graph_json_data)
        self.assertIn("nodes:", answer.graph_json_data)

    def test_large_automata_is_skipped(self):
        big_automata = "\n".join(
            f"{i}: C, {(i + 1) % 150}, {(i + 1) % 150}" for i in range(150)
        )
        answer = Answer.objects.create(
            game=self.game, player=self.player, automata=big_automata,
            initial_state="0", motivation="m", name="Big",
        )
        self.run_command(session=self.session.url_tag, game=self.game.url_tag)
        answer.refresh_from_db()
        self.assertIsNone(answer.graph_json_data)
