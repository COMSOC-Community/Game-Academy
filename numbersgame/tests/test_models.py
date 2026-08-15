from django.db import IntegrityError
from django.test import TestCase

from core.tests.helpers import make_session, make_user, make_game, make_player
from numbersgame.models import Setting, Answer, Result


class SettingModelTests(TestCase):
    def setUp(self):
        self.session = make_session("ngsettingsession")
        self.game = make_game(self.session, url_tag="numb")

    def test_default_values(self):
        setting = Setting.objects.create(game=self.game)
        self.assertEqual(setting.lower_bound, 0)
        self.assertEqual(setting.upper_bound, 100)
        self.assertEqual(setting.factor, 2 / 3)
        self.assertEqual(setting.factor_display, "2/3")
        self.assertEqual(setting.histogram_bin_size, 3)

    def test_one_to_one_with_game(self):
        setting = Setting.objects.create(game=self.game)
        self.assertEqual(self.game.numbers_setting, setting)

    def test_only_one_setting_per_game(self):
        Setting.objects.create(game=self.game)
        with self.assertRaises(IntegrityError):
            Setting.objects.create(game=self.game)


class AnswerModelTests(TestCase):
    def setUp(self):
        self.session = make_session("nganswersession")
        self.game = make_game(self.session, url_tag="numb")
        self.user = make_user("nganswerplayer")
        self.player = make_player(self.session, self.user)

    def test_str_without_winner(self):
        answer = Answer.objects.create(
            game=self.game, player=self.player, answer=42.0, motivation="m"
        )
        self.assertIn(self.player.name, str(answer))
        self.assertNotIn("(win)", str(answer))

    def test_str_with_winner(self):
        answer = Answer.objects.create(
            game=self.game, player=self.player, answer=42.0, motivation="m", winner=True
        )
        self.assertIn("(win)", str(answer))

    def test_unique_constraint_game_player(self):
        Answer.objects.create(game=self.game, player=self.player, answer=1, motivation="m")
        with self.assertRaises(IntegrityError):
            Answer.objects.create(game=self.game, player=self.player, answer=2, motivation="m2")

    def test_submission_time_is_auto_set(self):
        answer = Answer.objects.create(
            game=self.game, player=self.player, answer=1, motivation="m"
        )
        self.assertIsNotNone(answer.submission_time)


class ResultModelTests(TestCase):
    def setUp(self):
        self.session = make_session("ngresultsession")
        self.game = make_game(self.session, url_tag="numb")

    def test_one_to_one_with_game(self):
        result = Result.objects.create(game=self.game)
        self.assertEqual(self.game.result_ng, result)

    def test_str(self):
        result = Result.objects.create(game=self.game)
        self.assertEqual(str(result), f"{self.game.name} - Results Data")

    def test_only_one_result_per_game(self):
        Result.objects.create(game=self.game)
        with self.assertRaises(IntegrityError):
            Result.objects.create(game=self.game)
