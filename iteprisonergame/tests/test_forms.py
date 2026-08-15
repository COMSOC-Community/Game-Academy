from django.test import TestCase

from core.tests.helpers import make_session, make_user, make_player
from iteprisonergame.forms import SettingForm, SubmitAnswerForm
from iteprisonergame.models import Answer, Setting
from iteprisonergame.tests.helpers import (
    make_itepris_game,
    ALWAYS_COOPERATE,
    ALWAYS_DEFECT,
    TIT_FOR_TAT,
)


class SettingFormTests(TestCase):
    def setUp(self):
        self.session = make_session("ipdsettingformsession")
        self.game = make_itepris_game(self.session)

    def base_data(self, **overrides):
        data = {
            "num_repetitions": "100, 200",
            "store_scores": "on",
            "payoff_high": "0",
            "payoff_medium": "-10",
            "payoff_low": "-20",
            "payoff_tiny": "-25",
            "forbidden_strategies": "",
        }
        data.update(overrides)
        return data

    def test_valid_comma_separated_repetitions_accepted(self):
        form = SettingForm(data=self.base_data())
        self.assertTrue(form.is_valid())
        self.assertEqual(form.cleaned_data["num_repetitions"], "100,200")

    def test_single_repetition_is_cast_to_float(self):
        form = SettingForm(data=self.base_data(num_repetitions="150"))
        self.assertTrue(form.is_valid())
        self.assertEqual(form.cleaned_data["num_repetitions"], 150.0)

    def test_non_numeric_repetition_in_list_is_rejected(self):
        form = SettingForm(data=self.base_data(num_repetitions="100, abc"))
        self.assertFalse(form.is_valid())
        self.assertIn("num_repetitions", form.errors)

    def test_non_numeric_single_repetition_is_rejected(self):
        form = SettingForm(data=self.base_data(num_repetitions="abc"))
        self.assertFalse(form.is_valid())
        self.assertIn("num_repetitions", form.errors)

    def test_empty_forbidden_strategies_is_accepted(self):
        form = SettingForm(data=self.base_data())
        self.assertTrue(form.is_valid())

    def test_valid_forbidden_strategy_is_accepted(self):
        form = SettingForm(data=self.base_data(forbidden_strategies=ALWAYS_COOPERATE))
        self.assertTrue(form.is_valid())

    def test_malformed_forbidden_strategy_is_rejected(self):
        form = SettingForm(data=self.base_data(forbidden_strategies="not a valid automata"))
        self.assertFalse(form.is_valid())
        self.assertIn("forbidden_strategies", form.errors)

    def test_forbidden_strategy_that_parses_but_is_invalid_is_rejected(self):
        # "0: C, 0, 1" parses fine syntactically, but references state "1" which is never
        # itself defined -- a validity error, not a parse error.
        form = SettingForm(data=self.base_data(forbidden_strategies="0: C, 0, 1"))
        self.assertFalse(form.is_valid())
        self.assertIn("forbidden_strategies", form.errors)

    def test_multiple_forbidden_strategies_separated_by_dashes(self):
        form = SettingForm(
            data=self.base_data(
                forbidden_strategies=f"{ALWAYS_COOPERATE}\n---\n{TIT_FOR_TAT}"
            )
        )
        self.assertTrue(form.is_valid())


class SubmitAnswerFormTests(TestCase):
    def setUp(self):
        self.session = make_session("ipdformsession")
        self.game = make_itepris_game(self.session)
        Setting.objects.create(game=self.game)
        self.user = make_user("ipdformplayer")
        self.player = make_player(self.session, self.user)

    def base_data(self, **overrides):
        data = {
            "name": "My Strategy",
            "initial_state": "0",
            "automata": ALWAYS_COOPERATE,
            "motivation": "because",
        }
        data.update(overrides)
        return data

    def test_valid_strategy_is_accepted(self):
        form = SubmitAnswerForm(data=self.base_data(), game=self.game, player=self.player)
        self.assertTrue(form.is_valid())

    def test_malformed_automata_is_rejected(self):
        form = SubmitAnswerForm(
            data=self.base_data(automata="not valid"), game=self.game, player=self.player
        )
        self.assertFalse(form.is_valid())
        self.assertIn("automata", form.errors)

    def test_incomplete_automata_is_rejected(self):
        # References state "1" from state "0" but never defines it.
        form = SubmitAnswerForm(
            data=self.base_data(automata="0: C, 0, 1"), game=self.game, player=self.player
        )
        self.assertFalse(form.is_valid())
        self.assertIn("automata", form.errors)

    def test_initial_state_not_in_automata_is_rejected(self):
        form = SubmitAnswerForm(
            data=self.base_data(automata=ALWAYS_COOPERATE, initial_state="9"),
            game=self.game, player=self.player,
        )
        self.assertFalse(form.is_valid())
        self.assertIn("not part of the states", str(form.errors))

    def test_disconnected_automata_is_rejected(self):
        form = SubmitAnswerForm(
            data=self.base_data(automata="0: C, 0, 0\n1: D, 1, 1"),
            game=self.game, player=self.player,
        )
        self.assertFalse(form.is_valid())
        self.assertIn("connected components", str(form.errors))

    def test_missing_motivation_is_accepted(self):
        # Motivation is optional in this game.
        form = SubmitAnswerForm(
            data=self.base_data(motivation=""), game=self.game, player=self.player
        )
        self.assertTrue(form.is_valid())

    def test_duplicate_submission_is_rejected(self):
        Answer.objects.create(
            game=self.game, player=self.player, automata=ALWAYS_COOPERATE,
            initial_state="0", motivation="already submitted", name="Existing",
        )
        form = SubmitAnswerForm(data=self.base_data(), game=self.game, player=self.player)
        self.assertFalse(form.is_valid())
        self.assertIn("already submitted an answer", str(form.errors))

    def test_forbidden_strategy_is_rejected(self):
        self.game.itepris_setting.forbidden_strategies = ALWAYS_COOPERATE
        self.game.itepris_setting.save()
        form = SubmitAnswerForm(
            data=self.base_data(automata=ALWAYS_COOPERATE), game=self.game, player=self.player
        )
        self.assertFalse(form.is_valid())
        self.assertIn("forbidden", str(form.errors))

    def test_second_of_several_dash_separated_forbidden_strategies_is_rejected(self):
        self.game.itepris_setting.forbidden_strategies = (
            f"{ALWAYS_COOPERATE}\n---\n{ALWAYS_DEFECT}"
        )
        self.game.itepris_setting.save()
        form = SubmitAnswerForm(
            data=self.base_data(automata=ALWAYS_DEFECT), game=self.game, player=self.player
        )
        self.assertFalse(form.is_valid())
        self.assertIn("forbidden", str(form.errors))

    def test_isomorphic_variant_of_forbidden_strategy_is_rejected(self):
        self.game.itepris_setting.forbidden_strategies = ALWAYS_COOPERATE
        self.game.itepris_setting.save()
        # Same structure as ALWAYS_COOPERATE, just with a renamed state.
        form = SubmitAnswerForm(
            data=self.base_data(automata="a: C, a, a", initial_state="a"),
            game=self.game, player=self.player,
        )
        self.assertFalse(form.is_valid())
        self.assertIn("forbidden", str(form.errors))

    def test_non_forbidden_strategy_is_accepted(self):
        self.game.itepris_setting.forbidden_strategies = ALWAYS_COOPERATE
        self.game.itepris_setting.save()
        form = SubmitAnswerForm(
            data=self.base_data(automata=TIT_FOR_TAT), game=self.game, player=self.player
        )
        self.assertTrue(form.is_valid())
