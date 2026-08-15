from django.db import IntegrityError
from django.test import TestCase

from core.tests.helpers import make_session, make_user, make_player
from centipedegame.models import Setting, Answer, Result
from centipedegame.tests.helpers import make_centipede_game


class SettingModelTests(TestCase):
    def setUp(self):
        self.session = make_session("centisettingsession")
        self.game = make_centipede_game(self.session)

    def test_default_values(self):
        setting = Setting.objects.create(game=self.game)
        self.assertEqual(setting.payoff_d_p1, 10)
        self.assertEqual(setting.payoff_d_p2, 10)
        self.assertEqual(setting.payoff_rd_p1, 0)
        self.assertEqual(setting.payoff_rd_p2, 40)
        self.assertEqual(setting.payoff_rrd_p1, 30)
        self.assertEqual(setting.payoff_rrd_p2, 30)
        self.assertEqual(setting.payoff_rrrd_p1, 20)
        self.assertEqual(setting.payoff_rrrd_p2, 60)
        self.assertEqual(setting.payoff_rrrr_p1, 50)
        self.assertEqual(setting.payoff_rrrr_p2, 50)

    def test_one_to_one_with_game(self):
        setting = Setting.objects.create(game=self.game)
        self.assertEqual(self.game.centi_setting, setting)


class AnswerModelTests(TestCase):
    def setUp(self):
        self.session = make_session("centianswersession")
        self.game = make_centipede_game(self.session)
        self.user = make_user("centianswerplayer")
        self.player = make_player(self.session, self.user)

    def test_str(self):
        answer = Answer.objects.create(
            game=self.game, player=self.player,
            strategy_as_p1="Down - Down", strategy_as_p2="Right - Right", motivation="m",
        )
        self.assertIn(self.player.name, str(answer))
        self.assertIn("Down - Down", str(answer))
        self.assertIn("Right - Right", str(answer))

    def test_unique_together_game_player(self):
        Answer.objects.create(
            game=self.game, player=self.player,
            strategy_as_p1="Down - Down", strategy_as_p2="Down - Down", motivation="m",
        )
        with self.assertRaises(IntegrityError):
            Answer.objects.create(
                game=self.game, player=self.player,
                strategy_as_p1="Right - Right", strategy_as_p2="Right - Right", motivation="m2",
            )


class ResultModelTests(TestCase):
    def setUp(self):
        self.session = make_session("centiresultsession")
        self.game = make_centipede_game(self.session)

    def test_one_to_one_with_game(self):
        result = Result.objects.create(game=self.game)
        self.assertEqual(self.game.result_centi, result)

    def test_str(self):
        result = Result.objects.create(game=self.game)
        self.assertIn(self.game.name, str(result))
