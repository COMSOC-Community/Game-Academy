from django.test import TestCase

from core.tests.helpers import make_session, make_user, make_player
from simp_poker.forms import SubmitAnswerForm
from simp_poker.models import Answer
from simp_poker.tests.helpers import make_poker_game


class SubmitAnswerFormTests(TestCase):
    def setUp(self):
        self.session = make_session("spformsession")
        self.game = make_poker_game(self.session)
        self.user = make_user("spformplayer")
        self.player = make_player(self.session, self.user)

    def base_data(self, **overrides):
        data = {
            "prob_p1_king": "1",
            "prob_p1_queen": "0.5",
            "prob_p1_jack": "0.33",
            "prob_p2_king": "1",
            "prob_p2_queen": "0.33",
            "prob_p2_jack": "0",
            "motivation": "because",
        }
        data.update(overrides)
        return data

    def test_valid_data_is_accepted(self):
        form = SubmitAnswerForm(data=self.base_data(), game=self.game, player=self.player)
        self.assertTrue(form.is_valid())

    def test_probability_above_one_is_rejected(self):
        form = SubmitAnswerForm(
            data=self.base_data(prob_p1_king="1.5"), game=self.game, player=self.player
        )
        self.assertFalse(form.is_valid())
        self.assertIn("prob_p1_king", form.errors)

    def test_probability_below_zero_is_rejected(self):
        form = SubmitAnswerForm(
            data=self.base_data(prob_p2_jack="-0.1"), game=self.game, player=self.player
        )
        self.assertFalse(form.is_valid())
        self.assertIn("prob_p2_jack", form.errors)

    def test_missing_motivation_is_rejected(self):
        form = SubmitAnswerForm(
            data=self.base_data(motivation=""), game=self.game, player=self.player
        )
        self.assertFalse(form.is_valid())
        self.assertIn("motivation", form.errors)

    def test_duplicate_submission_is_rejected(self):
        Answer.objects.create(
            game=self.game, player=self.player,
            prob_p1_king=1, prob_p1_queen=1, prob_p1_jack=1,
            prob_p2_king=1, prob_p2_queen=1, prob_p2_jack=1,
            motivation="already submitted",
        )
        form = SubmitAnswerForm(data=self.base_data(), game=self.game, player=self.player)
        self.assertFalse(form.is_valid())
        self.assertIn("You have already submitted an answer", str(form.errors))
