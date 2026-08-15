from django.test import TestCase
from django.urls import reverse

from core.tests.helpers import make_session, make_user, make_game, make_player
from numbersgame.models import Answer, Setting


class NumbersGameViewTestsBase(TestCase):
    def setUp(self):
        self.session = make_session("ngviewsession", visible=True)
        self.game = make_game(self.session, url_tag="numb", visible=True, playable=True)
        Setting.objects.create(game=self.game, lower_bound=0, upper_bound=100)
        self.user = make_user("ngviewplayer")
        self.player = make_player(self.session, self.user)

    def index_url(self):
        return reverse(
            "numbers_game:index", args=(self.session.url_tag, self.game.url_tag)
        )

    def submit_url(self):
        return reverse(
            "numbers_game:submit_answer", args=(self.session.url_tag, self.game.url_tag)
        )

    def results_url(self):
        return reverse(
            "numbers_game:global_results", args=(self.session.url_tag, self.game.url_tag)
        )


class IndexViewTests(NumbersGameViewTestsBase):
    def test_get_renders_for_logged_in_player(self):
        self.client.login(username="ngviewplayer", password="pw")
        response = self.client.get(self.index_url())
        self.assertEqual(response.status_code, 200)
        self.assertFalse(response.context["game_nav_display_home"])


class SubmitAnswerViewGetTests(NumbersGameViewTestsBase):
    def test_shows_form_when_no_answer_yet(self):
        self.client.login(username="ngviewplayer", password="pw")
        response = self.client.get(self.submit_url())
        self.assertEqual(response.status_code, 200)
        self.assertIsNotNone(response.context["submit_answer_form"])

    def test_no_form_when_answer_already_submitted(self):
        Answer.objects.create(
            game=self.game, player=self.player, answer=10, motivation="m"
        )
        self.client.login(username="ngviewplayer", password="pw")
        response = self.client.get(self.submit_url())
        self.assertEqual(response.status_code, 200)
        self.assertNotIn("submit_answer_form", response.context)

    def test_non_playable_game_blocks_non_admin(self):
        self.game.playable = False
        self.game.save()
        self.client.login(username="ngviewplayer", password="pw")
        response = self.client.get(self.submit_url())
        self.assertEqual(response.status_code, 404)


class SubmitAnswerViewPostTests(NumbersGameViewTestsBase):
    def test_valid_submission_creates_answer(self):
        self.client.login(username="ngviewplayer", password="pw")
        response = self.client.post(
            self.submit_url(), {"answer": "42", "motivation": "reasoning"}
        )
        self.assertEqual(response.status_code, 200)
        answer = Answer.objects.get(game=self.game, player=self.player)
        self.assertEqual(answer.answer, 42)
        self.assertEqual(response.context["submitted_answer"], answer)

    def test_invalid_submission_re_renders_with_errors(self):
        self.client.login(username="ngviewplayer", password="pw")
        response = self.client.post(
            self.submit_url(), {"answer": "-5", "motivation": "reasoning"}
        )
        self.assertEqual(response.status_code, 200)
        self.assertFalse(Answer.objects.filter(game=self.game, player=self.player).exists())
        self.assertIn("submit_answer_form", response.context)
        self.assertTrue(response.context["submit_answer_form"].errors)

    def test_management_command_runs_when_flag_enabled(self):
        self.game.run_management_after_submit = True
        self.game.save()
        self.client.login(username="ngviewplayer", password="pw")
        self.client.post(self.submit_url(), {"answer": "42", "motivation": "reasoning"})
        self.game.refresh_from_db()
        self.assertIsNotNone(self.game.result_ng)
        self.assertEqual(self.game.result_ng.average, 42)


class ResultsViewTests(NumbersGameViewTestsBase):
    def test_no_answers_yet(self):
        self.client.login(username="ngviewplayer", password="pw")
        self.game.results_visible = True
        self.game.save()
        response = self.client.get(self.results_url())
        self.assertEqual(response.status_code, 200)
        self.assertNotIn("answers", response.context)

    def test_hidden_results_block_non_admin(self):
        self.game.results_visible = False
        self.game.save()
        self.client.login(username="ngviewplayer", password="pw")
        response = self.client.get(self.results_url())
        self.assertEqual(response.status_code, 404)

    def test_with_answers_and_winner(self):
        self.game.results_visible = True
        self.game.save()
        other_user = make_user("ngviewplayer2")
        other_player = make_player(self.session, other_user, name="ngviewplayer2")
        Answer.objects.create(
            game=self.game, player=self.player, answer=10, motivation="m", winner=True
        )
        Answer.objects.create(
            game=self.game, player=other_player, answer=90, motivation="m2", winner=False
        )
        self.client.login(username="ngviewplayer", password="pw")
        response = self.client.get(self.results_url())
        self.assertEqual(response.status_code, 200)
        self.assertEqual(len(response.context["answers"]), 2)
        self.assertEqual(len(response.context["winning_answers"]), 1)
        self.assertEqual(list(response.context["winning_numbers"]), [10])
