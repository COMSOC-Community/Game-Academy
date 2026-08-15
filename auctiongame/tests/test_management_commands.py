import io
from decimal import Decimal

from django.core.management import call_command
from django.test import TestCase

from core.tests.helpers import make_session, make_user, make_player
from auctiongame.models import Answer, Result
from auctiongame.tests.helpers import make_auction_game


class AuctGenerateGraphCommandTests(TestCase):
    def setUp(self):
        self.session = make_session("auctcmdsession")
        self.game = make_auction_game(self.session)

    def run_command(self, **kwargs):
        stderr = io.StringIO()
        stdout = io.StringIO()
        call_command("auct_generategraph", stderr=stderr, stdout=stdout, **kwargs)
        return stdout.getvalue(), stderr.getvalue()

    def make_bid(self, name, auction_id, valuation, bid, **overrides):
        user = make_user(name)
        player = make_player(self.session, user, name=name)
        data = dict(
            game=self.game, player=player, auction_id=auction_id, valuation=valuation,
            bid=Decimal(str(bid)) if bid is not None else None, motivation="m",
        )
        data.update(overrides)
        return Answer.objects.create(**data)

    def test_unknown_session_reports_error(self):
        _, stderr = self.run_command(session="doesnotexist", game=self.game.url_tag)
        self.assertIn("No session found", stderr)

    def test_unknown_game_reports_error(self):
        _, stderr = self.run_command(session=self.session.url_tag, game="doesnotexist")
        self.assertIn("No game found", stderr)

    def test_no_answers_does_nothing(self):
        self.run_command(session=self.session.url_tag, game=self.game.url_tag)
        self.assertFalse(Result.objects.filter(game=self.game).exists())

    def test_single_bidder_wins_their_own_auction(self):
        answer = self.make_bid("auctcmdp1", 1, 10, 4)
        self.run_command(session=self.session.url_tag, game=self.game.url_tag)
        answer.refresh_from_db()
        self.assertTrue(answer.winning_auction)
        self.assertTrue(answer.winning_global)
        self.assertEqual(answer.utility, Decimal("6"))

    def test_highest_bidder_wins_the_auction(self):
        winner = self.make_bid("auctcmdp2", 1, 10, 8)
        loser = self.make_bid("auctcmdp3", 1, 10, 3)
        self.run_command(session=self.session.url_tag, game=self.game.url_tag)
        winner.refresh_from_db()
        loser.refresh_from_db()
        self.assertTrue(winner.winning_auction)
        self.assertFalse(loser.winning_auction)
        self.assertEqual(loser.utility, Decimal("0"))

    def test_tied_highest_bids_both_win_the_auction(self):
        a1 = self.make_bid("auctcmdp4", 1, 10, 5)
        a2 = self.make_bid("auctcmdp5", 1, 10, 5)
        self.run_command(session=self.session.url_tag, game=self.game.url_tag)
        a1.refresh_from_db()
        a2.refresh_from_db()
        self.assertTrue(a1.winning_auction)
        self.assertTrue(a2.winning_auction)

    def test_global_winner_is_highest_utility_across_auctions(self):
        low_utility = self.make_bid("auctcmdp6", 1, 10, 9)  # utility 1
        high_utility = self.make_bid("auctcmdp7", 2, 10, 2)  # utility 8
        self.run_command(session=self.session.url_tag, game=self.game.url_tag)
        low_utility.refresh_from_db()
        high_utility.refresh_from_db()
        self.assertFalse(low_utility.winning_global)
        self.assertTrue(high_utility.winning_global)

    def test_result_row_created_per_auction_with_bids(self):
        self.make_bid("auctcmdp8", 1, 10, 5)
        self.make_bid("auctcmdp9", 2, 10, 5)
        self.run_command(session=self.session.url_tag, game=self.game.url_tag)
        self.assertEqual(Result.objects.filter(game=self.game).count(), 2)

    def test_result_row_created_even_for_auction_with_no_bids_yet(self):
        # An Answer was auto-assigned to auction 3 but no bid submitted yet: the command
        # still creates an (empty) Result row for that auction before skipping histogram
        # computation, since Result.objects.get_or_create runs before the "no bids" check.
        self.make_bid("auctcmdp10", 3, 10, None)
        self.run_command(session=self.session.url_tag, game=self.game.url_tag)
        result = Result.objects.get(game=self.game, auction_id=3)
        self.assertIsNone(result.histo_bids_js_data)

    def test_rerun_updates_result_without_duplicating(self):
        self.make_bid("auctcmdp11", 1, 10, 5)
        self.run_command(session=self.session.url_tag, game=self.game.url_tag)
        self.make_bid("auctcmdp12", 1, 10, 9)
        self.run_command(session=self.session.url_tag, game=self.game.url_tag)
        self.assertEqual(Result.objects.filter(game=self.game, auction_id=1).count(), 1)

    def test_histogram_data_is_populated(self):
        self.make_bid("auctcmdp13", 1, 10, 5)
        self.run_command(session=self.session.url_tag, game=self.game.url_tag)
        result = Result.objects.get(game=self.game, auction_id=1)
        self.assertIsNotNone(result.histo_bids_js_data)
        self.assertIsNotNone(result.histo_val_js_data)
