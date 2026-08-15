from django.test import TestCase
from django.urls import reverse

from core.tests.helpers import make_session, make_user, make_player
from simp_poker.models import Answer
from simp_poker.tests.helpers import make_poker_game


class SimpPokerViewTestsBase(TestCase):
    def setUp(self):
        self.session = make_session("spviewsession", visible=True)
        self.game = make_poker_game(self.session, visible=True, playable=True)
        self.user = make_user("spviewplayer")
        self.player = make_player(self.session, self.user)

    def index_url(self):
        return reverse("simp_poker:index", args=(self.session.url_tag, self.game.url_tag))

    def submit_url(self):
        return reverse(
            "simp_poker:submit_answer", args=(self.session.url_tag, self.game.url_tag)
        )

    def results_url(self):
        return reverse(
            "simp_poker:global_results", args=(self.session.url_tag, self.game.url_tag)
        )

    def valid_post_data(self, **overrides):
        data = {
            "prob_p1_king": "1", "prob_p1_queen": "0.5", "prob_p1_jack": "0.33",
            "prob_p2_king": "1", "prob_p2_queen": "0.33", "prob_p2_jack": "0",
            "motivation": "because",
        }
        data.update(overrides)
        return data


class IndexViewTests(SimpPokerViewTestsBase):
    def test_get_renders_for_logged_in_player(self):
        self.client.login(username="spviewplayer", password="pw")
        response = self.client.get(self.index_url())
        self.assertEqual(response.status_code, 200)


class SubmitAnswerViewGetTests(SimpPokerViewTestsBase):
    def test_shows_form_when_no_answer_yet(self):
        self.client.login(username="spviewplayer", password="pw")
        response = self.client.get(self.submit_url())
        self.assertEqual(response.status_code, 200)
        self.assertIsNotNone(response.context["submit_answer_form"])

    def test_non_playable_game_blocks_non_admin(self):
        self.game.playable = False
        self.game.save()
        self.client.login(username="spviewplayer", password="pw")
        response = self.client.get(self.submit_url())
        self.assertEqual(response.status_code, 404)


class SubmitAnswerViewPostTests(SimpPokerViewTestsBase):
    def test_valid_submission_creates_answer_and_computes_score(self):
        self.client.login(username="spviewplayer", password="pw")
        response = self.client.post(self.submit_url(), self.valid_post_data())
        self.assertEqual(response.status_code, 200)
        answer = Answer.objects.get(game=self.game, player=self.player)
        self.assertIsNotNone(answer.score_against_optimum)
        self.assertEqual(response.context["submitted_answer"], answer)

    def test_exact_optimal_strategy_scores_zero_against_optimum(self):
        self.client.login(username="spviewplayer", password="pw")
        self.client.post(
            self.submit_url(),
            self.valid_post_data(
                prob_p1_king="1", prob_p1_queen="1", prob_p1_jack="0.33333",
                prob_p2_king="1", prob_p2_queen="0.33333", prob_p2_jack="0",
            ),
        )
        answer = Answer.objects.get(game=self.game, player=self.player)
        self.assertAlmostEqual(answer.score_against_optimum, 0, places=3)

    def test_invalid_submission_re_renders_with_errors(self):
        self.client.login(username="spviewplayer", password="pw")
        response = self.client.post(
            self.submit_url(), self.valid_post_data(prob_p1_king="5")
        )
        self.assertEqual(response.status_code, 200)
        self.assertFalse(Answer.objects.filter(game=self.game, player=self.player).exists())
        self.assertTrue(response.context["submit_answer_form"].errors)

    def test_management_command_runs_when_flag_enabled(self):
        self.game.run_management_after_submit = True
        self.game.save()
        self.client.login(username="spviewplayer", password="pw")
        self.client.post(self.submit_url(), self.valid_post_data())
        self.game.refresh_from_db()
        self.assertIsNotNone(self.game.simp_poker_res)


class ResultsViewTests(SimpPokerViewTestsBase):
    def make_answer(self, name, **overrides):
        user = make_user(name)
        player = make_player(self.session, user, name=name)
        data = dict(
            game=self.game, player=player,
            prob_p1_king=1, prob_p1_queen=1, prob_p1_jack=0.33,
            prob_p2_king=1, prob_p2_queen=0.33, prob_p2_jack=0,
            motivation="m",
        )
        data.update(overrides)
        return Answer.objects.create(**data)

    def test_hidden_results_block_non_admin(self):
        self.game.results_visible = False
        self.game.save()
        self.client.login(username="spviewplayer", password="pw")
        response = self.client.get(self.results_url())
        self.assertEqual(response.status_code, 404)

    def test_no_answers_yet(self):
        self.game.results_visible = True
        self.game.save()
        self.client.login(username="spviewplayer", password="pw")
        response = self.client.get(self.results_url())
        self.assertEqual(response.status_code, 200)
        self.assertEqual(len(response.context["answers_sorted_round_robin"]), 0)

    def test_single_round_robin_winner_is_formatted(self):
        self.game.results_visible = True
        self.game.save()
        self.make_answer("spviewplayer_winner", round_robin_position=1)
        self.make_answer("spviewplayer_loser", round_robin_position=2)
        self.client.login(username="spviewplayer", password="pw")
        response = self.client.get(self.results_url())
        self.assertEqual(response.status_code, 200)
        self.assertNotIn("several_winners_round_robin", response.context)
        self.assertIn("spviewplayer_winner", response.context["formatted_round_robin_winners"])

    def test_multiple_round_robin_winners_are_formatted_with_and(self):
        self.game.results_visible = True
        self.game.save()
        self.make_answer("spviewplayer_tie1", round_robin_position=1)
        self.make_answer("spviewplayer_tie2", round_robin_position=1)
        self.client.login(username="spviewplayer", password="pw")
        response = self.client.get(self.results_url())
        self.assertTrue(response.context["several_winners_round_robin"])
        self.assertIn(" and ", response.context["formatted_round_robin_winners"])

    def test_winners_against_optimum_are_formatted(self):
        self.game.results_visible = True
        self.game.save()
        self.make_answer("spviewplayer_optwinner", winner_against_optimum=True)
        self.client.login(username="spviewplayer", password="pw")
        response = self.client.get(self.results_url())
        self.assertIn(
            "spviewplayer_optwinner", response.context["formatted_winners_against_opt"]
        )

    def test_multiple_winners_against_optimum_are_formatted_with_and(self):
        self.game.results_visible = True
        self.game.save()
        self.make_answer("spviewplayer_opttie1", winner_against_optimum=True)
        self.make_answer("spviewplayer_opttie2", winner_against_optimum=True)
        self.client.login(username="spviewplayer", password="pw")
        response = self.client.get(self.results_url())
        self.assertTrue(response.context["several_winners_against_opt"])
        self.assertIn(" and ", response.context["formatted_winners_against_opt"])
