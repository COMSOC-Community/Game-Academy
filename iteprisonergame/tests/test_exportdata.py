import csv
import io

from django.test import TestCase

from core.tests.helpers import make_session, make_user, make_player
from iteprisonergame.exportdata import answers_to_csv, settings_to_csv
from iteprisonergame.models import Answer, Setting
from iteprisonergame.tests.helpers import make_itepris_game, ALWAYS_COOPERATE


class AnswersToCsvTests(TestCase):
    def setUp(self):
        self.session = make_session("ipdexportsession")
        self.game = make_itepris_game(self.session)
        self.user = make_user("ipdexportplayer")
        self.player = make_player(self.session, self.user)

    def test_header_row(self):
        buffer = io.StringIO()
        answers_to_csv(buffer, self.game)
        rows = list(csv.reader(io.StringIO(buffer.getvalue())))
        self.assertEqual(
            rows[0],
            ["player_name", "is_team_player", "answer_name", "automata", "initial_state",
             "motivation", "avg_score", "winner", "submission_time"],
        )

    def test_answer_row_content(self):
        Answer.objects.create(
            game=self.game, player=self.player, automata=ALWAYS_COOPERATE,
            initial_state="0", motivation="reasoning", name="AC", avg_score=1.5, winner=True,
        )
        buffer = io.StringIO()
        answers_to_csv(buffer, self.game)
        rows = list(csv.reader(io.StringIO(buffer.getvalue())))
        self.assertEqual(rows[1][0], self.player.name)
        self.assertEqual(rows[1][2], "AC")
        self.assertEqual(rows[1][3], ALWAYS_COOPERATE)
        self.assertEqual(rows[1][4], "0")
        self.assertEqual(rows[1][6], "1.5")
        self.assertEqual(rows[1][7], "True")


class SettingsToCsvTests(TestCase):
    def setUp(self):
        self.session = make_session("ipdexportsettingsession")
        self.game = make_itepris_game(self.session)

    def test_no_setting_produces_empty_output(self):
        buffer = io.StringIO()
        settings_to_csv(buffer, self.game)
        self.assertEqual(buffer.getvalue(), "")

    def test_setting_row_content(self):
        Setting.objects.create(
            game=self.game, num_repetitions="10,20", payoff_high=1, payoff_medium=2,
            payoff_low=3, payoff_tiny=4, forbidden_strategies="",
        )
        buffer = io.StringIO()
        settings_to_csv(buffer, self.game)
        rows = list(csv.reader(io.StringIO(buffer.getvalue())))
        self.assertEqual(
            rows[0],
            ["num_repetitions", "payoff_high", "payoff_medium", "payoff_low", "payoff_tiny",
             "forbidden_strategies"],
        )
        self.assertEqual(rows[1], ["10,20", "1", "2", "3", "4", ""])
