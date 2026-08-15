import csv
import io

from django.test import TestCase

from core.tests.helpers import make_session, make_user, make_game, make_player
from numbersgame.exportdata import answers_to_csv, settings_to_csv
from numbersgame.models import Answer, Setting


class AnswersToCsvTests(TestCase):
    def setUp(self):
        self.session = make_session("ngexportanswersession")
        self.game = make_game(self.session, url_tag="numb")
        self.user = make_user("ngexportplayer")
        self.player = make_player(self.session, self.user)

    def test_header_row(self):
        buffer = io.StringIO()
        answers_to_csv(buffer, self.game)
        rows = list(csv.reader(io.StringIO(buffer.getvalue())))
        self.assertEqual(
            rows[0],
            ["player_name", "is_team_player", "answer", "motivation", "gap", "winner",
             "submission_time"],
        )

    def test_no_answers_only_header(self):
        buffer = io.StringIO()
        answers_to_csv(buffer, self.game)
        rows = list(csv.reader(io.StringIO(buffer.getvalue())))
        self.assertEqual(len(rows), 1)

    def test_answer_row_content(self):
        Answer.objects.create(
            game=self.game, player=self.player, answer=42.5, motivation="reasoning",
            gap=1.5, winner=True,
        )
        buffer = io.StringIO()
        answers_to_csv(buffer, self.game)
        rows = list(csv.reader(io.StringIO(buffer.getvalue())))
        self.assertEqual(rows[1][0], self.player.name)
        self.assertEqual(rows[1][2], "42.5")
        self.assertEqual(rows[1][3], "reasoning")
        self.assertEqual(rows[1][4], "1.5")
        self.assertEqual(rows[1][5], "True")

    def test_only_this_games_answers_are_included(self):
        other_game = make_game(self.session, url_tag="othr", name="Other")
        Answer.objects.create(
            game=other_game, player=self.player, answer=1, motivation="other game"
        )
        buffer = io.StringIO()
        answers_to_csv(buffer, self.game)
        rows = list(csv.reader(io.StringIO(buffer.getvalue())))
        self.assertEqual(len(rows), 1)


class SettingsToCsvTests(TestCase):
    def setUp(self):
        self.session = make_session("ngexportsettingsession")
        self.game = make_game(self.session, url_tag="numb")

    def test_no_setting_produces_empty_output(self):
        buffer = io.StringIO()
        settings_to_csv(buffer, self.game)
        self.assertEqual(buffer.getvalue(), "")

    def test_setting_row_content(self):
        Setting.objects.create(
            game=self.game, lower_bound=0.25, upper_bound=99.5, factor=0.5,
            factor_display="1/2", histogram_bin_size=5.5,
        )
        buffer = io.StringIO()
        settings_to_csv(buffer, self.game)
        rows = list(csv.reader(io.StringIO(buffer.getvalue())))
        self.assertEqual(rows[0], ["lower_bound", "upper_bound", "factor", "factor_display",
                                    "histogram_bin_size"])
        self.assertEqual(rows[1], ["0.25", "99.5", "0.5", "1/2", "5.5"])
