from decimal import Decimal

from django.test import TestCase

from core.tests.helpers import make_session, make_user, make_player
from auctiongame.forms import SubmitAnswerForm
from auctiongame.models import Answer
from auctiongame.tests.helpers import make_auction_game


class SubmitAnswerFormTests(TestCase):
    def setUp(self):
        self.session = make_session("auctformsession")
        self.game = make_auction_game(self.session)
        self.user = make_user("auctformplayer")
        self.player = make_player(self.session, self.user)

    def test_no_pending_answer_object_is_rejected(self):
        form = SubmitAnswerForm(
            data={"bid": "5", "motivation": "because"}, game=self.game, player=self.player
        )
        self.assertFalse(form.is_valid())
        self.assertIn("not initialised", str(form.errors))

    def test_valid_bid_on_pending_answer_is_accepted(self):
        Answer.objects.create(
            game=self.game, player=self.player, auction_id=1, valuation=10, motivation=""
        )
        form = SubmitAnswerForm(
            data={"bid": "5.5", "motivation": "because"}, game=self.game, player=self.player
        )
        self.assertTrue(form.is_valid())
        self.assertEqual(form.cleaned_data["bid"], Decimal("5.5"))

    def test_already_submitted_bid_is_rejected(self):
        Answer.objects.create(
            game=self.game, player=self.player, auction_id=1, valuation=10,
            bid=Decimal("3"), motivation="already submitted",
        )
        form = SubmitAnswerForm(
            data={"bid": "5.5", "motivation": "because"}, game=self.game, player=self.player
        )
        self.assertFalse(form.is_valid())
        self.assertIn("You have already submitted an answer", str(form.errors))

    def test_negative_bid_is_rejected(self):
        Answer.objects.create(
            game=self.game, player=self.player, auction_id=1, valuation=10, motivation=""
        )
        form = SubmitAnswerForm(
            data={"bid": "-1", "motivation": "because"}, game=self.game, player=self.player
        )
        self.assertFalse(form.is_valid())
        self.assertIn("bid", form.errors)

    def test_non_numeric_bid_is_rejected(self):
        Answer.objects.create(
            game=self.game, player=self.player, auction_id=1, valuation=10, motivation=""
        )
        form = SubmitAnswerForm(
            data={"bid": "not-a-number", "motivation": "because"},
            game=self.game,
            player=self.player,
        )
        self.assertFalse(form.is_valid())
        self.assertIn("bid", form.errors)

    def test_missing_motivation_is_rejected(self):
        Answer.objects.create(
            game=self.game, player=self.player, auction_id=1, valuation=10, motivation=""
        )
        form = SubmitAnswerForm(
            data={"bid": "5", "motivation": ""}, game=self.game, player=self.player
        )
        self.assertFalse(form.is_valid())
        self.assertIn("motivation", form.errors)
