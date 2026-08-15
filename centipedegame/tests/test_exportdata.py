import csv
import io

from django.test import TestCase

from core.tests.helpers import make_session, make_user, make_player
from centipedegame.exportdata import answers_to_csv, settings_to_csv
from centipedegame.models import Answer, Setting
from centipedegame.tests.helpers import make_centipede_game


class AnswersToCsvTests(TestCase):
    def setUp(self):
        self.session = make_session("centiexportsession")
        self.game = make_centipede_game(self.session)
        self.user = make_user("centiexportplayer")
        self.player = make_player(self.session, self.user)

    def test_header_row(self):
        buffer = io.StringIO()
        answers_to_csv(buffer, self.game)
        rows = list(csv.reader(io.StringIO(buffer.getvalue())))
        self.assertEqual(
            rows[0],
            ["player_name", "is_team_player", "strategy_as_p1", "strategy_as_p2",
             "avg_score_as_p1", "avg_score_as_p2", "avg_score", "winning", "motivation",
             "submission_time"],
        )

    def test_answer_row_content(self):
        Answer.objects.create(
            game=self.game, player=self.player,
            strategy_as_p1="Down - Down", strategy_as_p2="Right - Right",
            avg_score=42, winning=True, motivation="reasoning",
        )
        buffer = io.StringIO()
        answers_to_csv(buffer, self.game)
        rows = list(csv.reader(io.StringIO(buffer.getvalue())))
        self.assertEqual(rows[1][0], self.player.name)
        self.assertEqual(rows[1][2], "Down - Down")
        self.assertEqual(rows[1][3], "Right - Right")
        self.assertEqual(rows[1][6], "42.0")
        self.assertEqual(rows[1][7], "True")
        self.assertEqual(rows[1][8], "reasoning")


class SettingsToCsvTests(TestCase):
    def setUp(self):
        self.session = make_session("centiexportsettingsession")
        self.game = make_centipede_game(self.session)

    def test_no_setting_produces_empty_output(self):
        buffer = io.StringIO()
        settings_to_csv(buffer, self.game)
        self.assertEqual(buffer.getvalue(), "")

    def test_setting_row_content(self):
        Setting.objects.create(game=self.game)
        buffer = io.StringIO()
        settings_to_csv(buffer, self.game)
        rows = list(csv.reader(io.StringIO(buffer.getvalue())))
        self.assertEqual(
            rows[0],
            ["payoff_d_p1", "payoff_d_p2", "payoff_rd_p1", "payoff_rd_p2",
             "payoff_rrd_p1", "payoff_rrd_p2", "payoff_rrrd_p1", "payoff_rrrd_p2",
             "payoff_rrrr_p1", "payoff_rrrr_p2"],
        )
        self.assertEqual(rows[1], ["10", "10", "0", "40", "30", "30", "20", "60", "50", "50"])
