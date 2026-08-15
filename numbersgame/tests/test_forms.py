from django.test import TestCase

from core.tests.helpers import make_session, make_user, make_game, make_player
from numbersgame.forms import SettingForm, SubmitAnswerForm
from numbersgame.models import Answer, Setting


class SettingFormTests(TestCase):
    def setUp(self):
        self.session = make_session("ngsettingformsession")
        self.game = make_game(self.session, url_tag="numb")

    def base_data(self, **overrides):
        data = {
            "lower_bound": "0",
            "upper_bound": "100",
            "factor": "0.6667",
            "factor_display": "2/3",
            "histogram_bin_size": "3",
        }
        data.update(overrides)
        return data

    def test_valid_data_is_accepted(self):
        form = SettingForm(data=self.base_data())
        self.assertTrue(form.is_valid())

    def test_histogram_bin_size_zero_is_rejected(self):
        form = SettingForm(data=self.base_data(histogram_bin_size="0"))
        self.assertFalse(form.is_valid())
        self.assertIn("histogram_bin_size", form.errors)

    def test_histogram_bin_size_negative_is_rejected(self):
        form = SettingForm(data=self.base_data(histogram_bin_size="-1"))
        self.assertFalse(form.is_valid())
        self.assertIn("histogram_bin_size", form.errors)

    def test_histogram_bin_size_above_100_is_rejected(self):
        form = SettingForm(data=self.base_data(histogram_bin_size="101"))
        self.assertFalse(form.is_valid())
        self.assertIn("histogram_bin_size", form.errors)

    def test_lower_bound_greater_than_upper_bound_is_rejected(self):
        form = SettingForm(data=self.base_data(lower_bound="100", upper_bound="0"))
        self.assertFalse(form.is_valid())
        self.assertIn("lower_bound", form.errors)

    def test_lower_bound_equal_to_upper_bound_is_accepted(self):
        form = SettingForm(data=self.base_data(lower_bound="50", upper_bound="50"))
        self.assertTrue(form.is_valid())

    def test_saves_to_setting_instance(self):
        form = SettingForm(data=self.base_data())
        self.assertTrue(form.is_valid())
        setting = form.save(commit=False)
        setting.game = self.game
        setting.save()
        self.assertEqual(Setting.objects.get(game=self.game).lower_bound, 0)


class SubmitAnswerFormTests(TestCase):
    def setUp(self):
        self.session = make_session("ngsubmitformsession")
        self.game = make_game(self.session, url_tag="numb")
        Setting.objects.create(game=self.game, lower_bound=0, upper_bound=100)
        self.user = make_user("ngsubmitformplayer")
        self.player = make_player(self.session, self.user)

    def test_valid_answer_in_bounds_is_accepted(self):
        form = SubmitAnswerForm(
            data={"answer": "50", "motivation": "because"}, game=self.game, player=self.player
        )
        self.assertTrue(form.is_valid())

    def test_answer_below_lower_bound_is_rejected(self):
        form = SubmitAnswerForm(
            data={"answer": "-1", "motivation": "because"}, game=self.game, player=self.player
        )
        self.assertFalse(form.is_valid())
        self.assertIn("answer", form.errors)

    def test_answer_above_upper_bound_is_rejected(self):
        form = SubmitAnswerForm(
            data={"answer": "101", "motivation": "because"}, game=self.game, player=self.player
        )
        self.assertFalse(form.is_valid())
        self.assertIn("answer", form.errors)

    def test_answer_at_bounds_is_accepted(self):
        form = SubmitAnswerForm(
            data={"answer": "0", "motivation": "because"}, game=self.game, player=self.player
        )
        self.assertTrue(form.is_valid())
        form = SubmitAnswerForm(
            data={"answer": "100", "motivation": "because"}, game=self.game, player=self.player
        )
        self.assertTrue(form.is_valid())

    def test_non_numeric_answer_is_rejected(self):
        form = SubmitAnswerForm(
            data={"answer": "not-a-number", "motivation": "because"},
            game=self.game,
            player=self.player,
        )
        self.assertFalse(form.is_valid())
        self.assertIn("answer", form.errors)

    def test_duplicate_submission_is_rejected(self):
        Answer.objects.create(
            game=self.game, player=self.player, answer=10, motivation="already submitted"
        )
        form = SubmitAnswerForm(
            data={"answer": "50", "motivation": "because"}, game=self.game, player=self.player
        )
        self.assertFalse(form.is_valid())
        self.assertIn("You have already submitted an answer", str(form.errors))

    def test_missing_motivation_is_rejected(self):
        form = SubmitAnswerForm(
            data={"answer": "50", "motivation": ""}, game=self.game, player=self.player
        )
        self.assertFalse(form.is_valid())
        self.assertIn("motivation", form.errors)
