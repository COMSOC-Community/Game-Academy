from django.test import TestCase

from core.tests.helpers import make_session, make_user, make_player
from centipedegame.forms import SubmitAnswerForm
from centipedegame.models import Answer
from centipedegame.tests.helpers import make_centipede_game


class SubmitAnswerFormTests(TestCase):
    def setUp(self):
        self.session = make_session("centiformsession")
        self.game = make_centipede_game(self.session)
        self.user = make_user("centiformplayer")
        self.player = make_player(self.session, self.user)

    def base_data(self, **overrides):
        data = {
            "strategy_as_p1": "Down - Down",
            "strategy_as_p2": "Right - Right",
            "motivation": "because",
        }
        data.update(overrides)
        return data

    def test_valid_data_is_accepted(self):
        form = SubmitAnswerForm(data=self.base_data(), game=self.game, player=self.player)
        self.assertTrue(form.is_valid())

    def test_invalid_strategy_choice_is_rejected(self):
        form = SubmitAnswerForm(
            data=self.base_data(strategy_as_p1="Not - A - Strategy"),
            game=self.game, player=self.player,
        )
        self.assertFalse(form.is_valid())
        self.assertIn("strategy_as_p1", form.errors)

    def test_missing_strategy_as_p1_is_rejected(self):
        form = SubmitAnswerForm(
            data=self.base_data(strategy_as_p1=""), game=self.game, player=self.player
        )
        self.assertFalse(form.is_valid())
        self.assertIn("strategy_as_p1", form.errors)

    def test_missing_motivation_is_rejected(self):
        form = SubmitAnswerForm(
            data=self.base_data(motivation=""), game=self.game, player=self.player
        )
        self.assertFalse(form.is_valid())
        self.assertIn("motivation", form.errors)

    def test_duplicate_submission_is_rejected(self):
        Answer.objects.create(
            game=self.game, player=self.player,
            strategy_as_p1="Down - Down", strategy_as_p2="Down - Down",
            motivation="already submitted",
        )
        form = SubmitAnswerForm(data=self.base_data(), game=self.game, player=self.player)
        self.assertFalse(form.is_valid())
        self.assertIn("You have already submitted an answer", str(form.errors))
