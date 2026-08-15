from django.test import TestCase
from django.urls import reverse

from core.tests.helpers import make_session, make_user, make_player
from centipedegame.models import Answer, Setting
from centipedegame.tests.helpers import make_centipede_game


class CentipedeGameViewTestsBase(TestCase):
    def setUp(self):
        self.session = make_session("centiviewsession", visible=True)
        self.game = make_centipede_game(self.session, visible=True, playable=True)
        Setting.objects.create(game=self.game)
        self.user = make_user("centiviewplayer")
        self.player = make_player(self.session, self.user)

    def index_url(self):
        return reverse(
            "centipede_game:index", args=(self.session.url_tag, self.game.url_tag)
        )

    def submit_url(self):
        return reverse(
            "centipede_game:submit_answer", args=(self.session.url_tag, self.game.url_tag)
        )

    def results_url(self):
        return reverse(
            "centipede_game:global_results", args=(self.session.url_tag, self.game.url_tag)
        )


class IndexViewTests(CentipedeGameViewTestsBase):
    def test_get_renders_for_logged_in_player(self):
        self.client.login(username="centiviewplayer", password="pw")
        response = self.client.get(self.index_url())
        self.assertEqual(response.status_code, 200)


class SubmitAnswerViewGetTests(CentipedeGameViewTestsBase):
    def test_shows_form_when_no_answer_yet(self):
        self.client.login(username="centiviewplayer", password="pw")
        response = self.client.get(self.submit_url())
        self.assertEqual(response.status_code, 200)
        self.assertIsNotNone(response.context["submit_answer_form"])

    def test_no_form_when_answer_already_submitted(self):
        Answer.objects.create(
            game=self.game, player=self.player,
            strategy_as_p1="Down - Down", strategy_as_p2="Down - Down", motivation="m",
        )
        self.client.login(username="centiviewplayer", password="pw")
        response = self.client.get(self.submit_url())
        self.assertEqual(response.status_code, 200)
        self.assertNotIn("submit_answer_form", response.context)

    def test_non_playable_game_blocks_non_admin(self):
        self.game.playable = False
        self.game.save()
        self.client.login(username="centiviewplayer", password="pw")
        response = self.client.get(self.submit_url())
        self.assertEqual(response.status_code, 404)


class SubmitAnswerViewPostTests(CentipedeGameViewTestsBase):
    def test_valid_submission_creates_answer(self):
        self.client.login(username="centiviewplayer", password="pw")
        response = self.client.post(
            self.submit_url(),
            {
                "strategy_as_p1": "Right - Down",
                "strategy_as_p2": "Right - Right",
                "motivation": "reasoning",
            },
        )
        self.assertEqual(response.status_code, 200)
        answer = Answer.objects.get(game=self.game, player=self.player)
        self.assertEqual(answer.strategy_as_p1, "Right - Down")
        self.assertEqual(answer.strategy_as_p2, "Right - Right")
        self.assertEqual(response.context["submitted_answer"], answer)

    def test_invalid_submission_re_renders_with_errors(self):
        self.client.login(username="centiviewplayer", password="pw")
        response = self.client.post(
            self.submit_url(),
            {"strategy_as_p1": "Bogus", "strategy_as_p2": "Right - Right",
             "motivation": "reasoning"},
        )
        self.assertEqual(response.status_code, 200)
        self.assertFalse(Answer.objects.filter(game=self.game, player=self.player).exists())
        self.assertTrue(response.context["submit_answer_form"].errors)

    def test_management_command_runs_when_flag_enabled(self):
        self.game.run_management_after_submit = True
        self.game.save()
        self.client.login(username="centiviewplayer", password="pw")
        self.client.post(
            self.submit_url(),
            {"strategy_as_p1": "Down - Down", "strategy_as_p2": "Down - Down",
             "motivation": "reasoning"},
        )
        self.game.refresh_from_db()
        self.assertIsNotNone(self.game.result_centi)


class ResultsViewTests(CentipedeGameViewTestsBase):
    def make_answer(self, name, **overrides):
        user = make_user(name)
        player = make_player(self.session, user, name=name)
        data = dict(
            game=self.game, player=player,
            strategy_as_p1="Down - Down", strategy_as_p2="Down - Down", motivation="m",
            avg_score=0,
        )
        data.update(overrides)
        return Answer.objects.create(**data)

    def test_hidden_results_block_non_admin(self):
        self.game.results_visible = False
        self.game.save()
        self.client.login(username="centiviewplayer", password="pw")
        response = self.client.get(self.results_url())
        self.assertEqual(response.status_code, 404)

    def test_no_answers_yet(self):
        self.game.results_visible = True
        self.game.save()
        self.client.login(username="centiviewplayer", password="pw")
        response = self.client.get(self.results_url())
        self.assertEqual(response.status_code, 200)
        self.assertEqual(len(response.context["answers"]), 0)
        self.assertNotIn("winning_answers", response.context)

    def test_single_winner_is_formatted(self):
        self.game.results_visible = True
        self.game.save()
        self.make_answer("centiviewwinner", avg_score=42, winning=True)
        self.make_answer("centiviewloser", avg_score=10, winning=False)
        self.client.login(username="centiviewplayer", password="pw")
        response = self.client.get(self.results_url())
        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.context["winning_answers_formatted"], "42.0")
        self.assertEqual(response.context["winners_formatted"], "centiviewwinner")

    def test_multiple_winners_are_formatted_with_and(self):
        self.game.results_visible = True
        self.game.save()
        self.make_answer("centiviewtie1", avg_score=20, winning=True)
        self.make_answer("centiviewtie2", avg_score=20, winning=True)
        self.client.login(username="centiviewplayer", password="pw")
        response = self.client.get(self.results_url())
        self.assertIn("and ", response.context["winners_formatted"])

    def test_winners_with_distinct_scores_are_both_shown(self):
        # winning_answers_formatted is built from the *distinct* avg_score values among
        # winners, which is a different branch from winners sharing one identical score.
        self.game.results_visible = True
        self.game.save()
        self.make_answer("centiviewdistinct1", avg_score=20, winning=True)
        self.make_answer("centiviewdistinct2", avg_score=30, winning=True)
        self.client.login(username="centiviewplayer", password="pw")
        response = self.client.get(self.results_url())
        self.assertIn("and", response.context["winning_answers_formatted"])
        self.assertIn("20", response.context["winning_answers_formatted"])
        self.assertIn("30", response.context["winning_answers_formatted"])
