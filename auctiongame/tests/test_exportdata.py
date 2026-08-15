import csv
import io
from decimal import Decimal

from django.test import TestCase

from core.tests.helpers import make_session, make_user, make_player
from auctiongame.exportdata import answers_to_csv, settings_to_csv
from auctiongame.models import Answer, Setting
from auctiongame.tests.helpers import make_auction_game


class AnswersToCsvTests(TestCase):
    def setUp(self):
        self.session = make_session("auctexportsession")
        self.game = make_auction_game(self.session)
        self.user = make_user("auctexportplayer")
        self.player = make_player(self.session, self.user)

    def test_header_row(self):
        buffer = io.StringIO()
        answers_to_csv(buffer, self.game)
        rows = list(csv.reader(io.StringIO(buffer.getvalue())))
        self.assertEqual(
            rows[0],
            ["player_name", "is_team_player", "auction_id", "bid", "utility",
             "winning_auction", "winning_global", "motivation", "submission_time"],
        )

    def test_answer_row_content(self):
        Answer.objects.create(
            game=self.game, player=self.player, auction_id=1, valuation=10,
            bid=Decimal("4.5"), utility=Decimal("5.5"), winning_auction=True,
            motivation="reasoning",
        )
        buffer = io.StringIO()
        answers_to_csv(buffer, self.game)
        rows = list(csv.reader(io.StringIO(buffer.getvalue())))
        self.assertEqual(rows[1][0], self.player.name)
        self.assertEqual(rows[1][2], "1")
        self.assertEqual(rows[1][3], "4.5")
        self.assertEqual(rows[1][4], "5.5")
        self.assertEqual(rows[1][5], "True")
        self.assertEqual(rows[1][7], "reasoning")


class SettingsToCsvTests(TestCase):
    def setUp(self):
        self.session = make_session("auctexportsettingsession")
        self.game = make_auction_game(self.session)

    def test_no_setting_produces_empty_output(self):
        buffer = io.StringIO()
        settings_to_csv(buffer, self.game)
        self.assertEqual(buffer.getvalue(), "")

    def test_setting_row_content(self):
        Setting.objects.create(game=self.game, number_auctions=7)
        buffer = io.StringIO()
        settings_to_csv(buffer, self.game)
        rows = list(csv.reader(io.StringIO(buffer.getvalue())))
        self.assertEqual(rows[0], ["number_auctions"])
        self.assertEqual(rows[1], ["7"])
