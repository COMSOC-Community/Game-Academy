from decimal import Decimal

from django.test import TestCase
from django.urls import reverse

from core.tests.helpers import make_session, make_user, make_player
from auctiongame.models import Answer, Setting
from auctiongame.tests.helpers import make_auction_game


class AuctionGameViewTestsBase(TestCase):
    def setUp(self):
        self.session = make_session("auctviewsession", visible=True)
        self.game = make_auction_game(self.session, visible=True, playable=True)
        Setting.objects.create(game=self.game, number_auctions=5, valuation_sampler="constant")
        self.user = make_user("auctviewplayer")
        self.player = make_player(self.session, self.user)

    def index_url(self):
        return reverse("auction_game:index", args=(self.session.url_tag, self.game.url_tag))

    def submit_url(self):
        return reverse(
            "auction_game:submit_answer", args=(self.session.url_tag, self.game.url_tag)
        )

    def results_url(self):
        return reverse(
            "auction_game:global_results", args=(self.session.url_tag, self.game.url_tag)
        )


class IndexViewTests(AuctionGameViewTestsBase):
    def test_get_renders_before_any_answer(self):
        self.client.login(username="auctviewplayer", password="pw")
        response = self.client.get(self.index_url())
        self.assertEqual(response.status_code, 200)

    def test_nav_answer_link_shown_when_bid_pending(self):
        Answer.objects.create(
            game=self.game, player=self.player, auction_id=1, valuation=10, motivation=""
        )
        self.client.login(username="auctviewplayer", password="pw")
        response = self.client.get(self.index_url())
        self.assertTrue(response.context["game_nav_display_answer"])


class SubmitAnswerViewGetTests(AuctionGameViewTestsBase):
    def test_first_visit_creates_pending_answer_with_no_bid(self):
        self.client.login(username="auctviewplayer", password="pw")
        response = self.client.get(self.submit_url())
        self.assertEqual(response.status_code, 200)
        answer = Answer.objects.get(game=self.game, player=self.player)
        self.assertIsNone(answer.bid)
        self.assertEqual(answer.valuation, 10 + answer.auction_id)
        self.assertIsNotNone(response.context["submit_answer_form"])

    def test_second_visit_does_not_create_a_second_answer(self):
        self.client.login(username="auctviewplayer", password="pw")
        self.client.get(self.submit_url())
        self.client.get(self.submit_url())
        self.assertEqual(Answer.objects.filter(game=self.game, player=self.player).count(), 1)

    def test_no_form_once_bid_already_submitted(self):
        Answer.objects.create(
            game=self.game, player=self.player, auction_id=1, valuation=10,
            bid=Decimal("5"), motivation="m",
        )
        self.client.login(username="auctviewplayer", password="pw")
        response = self.client.get(self.submit_url())
        self.assertEqual(response.status_code, 200)
        self.assertNotIn("submit_answer_form", response.context)

    def test_non_playable_game_blocks_non_admin(self):
        self.game.playable = False
        self.game.save()
        self.client.login(username="auctviewplayer", password="pw")
        response = self.client.get(self.submit_url())
        self.assertEqual(response.status_code, 404)


class SubmitAnswerViewPostTests(AuctionGameViewTestsBase):
    def test_post_without_prior_get_is_rejected(self):
        self.client.login(username="auctviewplayer", password="pw")
        response = self.client.post(
            self.submit_url(), {"bid": "5", "motivation": "because"}
        )
        self.assertEqual(response.status_code, 200)
        self.assertFalse(Answer.objects.filter(game=self.game, player=self.player).exists())

    def test_valid_bid_updates_pending_answer_and_computes_utility(self):
        answer = Answer.objects.create(
            game=self.game, player=self.player, auction_id=1, valuation=10, motivation=""
        )
        self.client.login(username="auctviewplayer", password="pw")
        response = self.client.post(
            self.submit_url(), {"bid": "4", "motivation": "because"}
        )
        self.assertEqual(response.status_code, 200)
        answer.refresh_from_db()
        self.assertEqual(answer.bid, Decimal("4"))
        self.assertEqual(answer.utility, Decimal("6"))
        self.assertEqual(response.context["submitted_answer"], answer)

    def test_invalid_bid_re_renders_with_errors(self):
        Answer.objects.create(
            game=self.game, player=self.player, auction_id=1, valuation=10, motivation=""
        )
        self.client.login(username="auctviewplayer", password="pw")
        response = self.client.post(
            self.submit_url(), {"bid": "-1", "motivation": "because"}
        )
        self.assertEqual(response.status_code, 200)
        self.assertTrue(response.context["submit_answer_form"].errors)

    def test_management_command_runs_when_flag_enabled(self):
        Answer.objects.create(
            game=self.game, player=self.player, auction_id=1, valuation=10, motivation=""
        )
        self.game.run_management_after_submit = True
        self.game.save()
        self.client.login(username="auctviewplayer", password="pw")
        self.client.post(self.submit_url(), {"bid": "4", "motivation": "because"})
        from auctiongame.models import Result
        self.assertTrue(Result.objects.filter(game=self.game, auction_id=1).exists())


class ResultsViewTests(AuctionGameViewTestsBase):
    def make_bid(self, name, auction_id, bid, **overrides):
        user = make_user(name)
        player = make_player(self.session, user, name=name)
        data = dict(
            game=self.game, player=player, auction_id=auction_id, valuation=10,
            bid=Decimal(str(bid)), motivation="m",
        )
        data.update(overrides)
        return Answer.objects.create(**data)

    def test_hidden_results_block_non_admin(self):
        self.game.results_visible = False
        self.game.save()
        self.client.login(username="auctviewplayer", password="pw")
        response = self.client.get(self.results_url())
        self.assertEqual(response.status_code, 404)

    def test_no_bids_yet(self):
        self.game.results_visible = True
        self.game.save()
        self.client.login(username="auctviewplayer", password="pw")
        response = self.client.get(self.results_url())
        self.assertEqual(response.status_code, 200)
        self.assertEqual(len(response.context["answers"]), 0)

    def test_single_auction_winner_is_formatted(self):
        self.game.results_visible = True
        self.game.save()
        self.make_bid(
            "auctviewwinner", 1, "10", winning_auction=True, winning_global=True
        )
        self.make_bid("auctviewloser", 1, "3")
        self.client.login(username="auctviewplayer", password="pw")
        response = self.client.get(self.results_url())
        self.assertEqual(response.status_code, 200)
        winning_answers, formatted = response.context["formatted_winners"][1]
        self.assertEqual(formatted, "auctviewwinner")
        self.assertEqual(response.context["global_winners_formatted"], "auctviewwinner")

    def test_three_way_auction_tie_is_formatted_with_commas_and_and(self):
        self.game.results_visible = True
        self.game.save()
        self.make_bid("auctviewthree1", 1, "10", winning_auction=True)
        self.make_bid("auctviewthree2", 1, "10", winning_auction=True)
        self.make_bid("auctviewthree3", 1, "10", winning_auction=True)
        self.client.login(username="auctviewplayer", password="pw")
        response = self.client.get(self.results_url())
        winning_answers, formatted = response.context["formatted_winners"][1]
        self.assertEqual(formatted, "auctviewthree1, auctviewthree2 and auctviewthree3")

    def test_multiple_global_winners_are_formatted_with_and(self):
        self.game.results_visible = True
        self.game.save()
        self.make_bid("auctviewtie1", 1, "10", winning_global=True, winning_auction=True)
        self.make_bid("auctviewtie2", 2, "10", winning_global=True, winning_auction=True)
        self.client.login(username="auctviewplayer", password="pw")
        response = self.client.get(self.results_url())
        self.assertIn("and ", response.context["global_winners_formatted"])
