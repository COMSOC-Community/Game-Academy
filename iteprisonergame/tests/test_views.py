from django.test import TestCase
from django.urls import reverse

from core.tests.helpers import make_session, make_user, make_player
from iteprisonergame.models import Answer, Setting
from iteprisonergame.tests.helpers import make_itepris_game, ALWAYS_COOPERATE, TIT_FOR_TAT


class ItePrisonerGameViewTestsBase(TestCase):
    def setUp(self):
        self.session = make_session("ipdviewsession", visible=True)
        self.game = make_itepris_game(self.session, visible=True, playable=True)
        Setting.objects.create(game=self.game)
        self.user = make_user("ipdviewplayer")
        self.player = make_player(self.session, self.user)

    def index_url(self):
        return reverse("itepris_game:index", args=(self.session.url_tag, self.game.url_tag))

    def submit_url(self):
        return reverse(
            "itepris_game:submit_answer", args=(self.session.url_tag, self.game.url_tag)
        )

    def results_url(self):
        return reverse(
            "itepris_game:global_results", args=(self.session.url_tag, self.game.url_tag)
        )

    def valid_post_data(self, **overrides):
        data = {
            "name": "My Strategy",
            "initial_state": "0",
            "automata": ALWAYS_COOPERATE,
            "motivation": "because",
        }
        data.update(overrides)
        return data


class IndexViewTests(ItePrisonerGameViewTestsBase):
    def test_get_renders_for_logged_in_player(self):
        self.client.login(username="ipdviewplayer", password="pw")
        response = self.client.get(self.index_url())
        self.assertEqual(response.status_code, 200)


class SubmitAnswerViewGetTests(ItePrisonerGameViewTestsBase):
    def test_shows_form_when_no_answer_yet(self):
        self.client.login(username="ipdviewplayer", password="pw")
        response = self.client.get(self.submit_url())
        self.assertEqual(response.status_code, 200)
        self.assertIsNotNone(response.context["submit_answer_form"])

    def test_non_playable_game_blocks_non_admin(self):
        self.game.playable = False
        self.game.save()
        self.client.login(username="ipdviewplayer", password="pw")
        response = self.client.get(self.submit_url())
        self.assertEqual(response.status_code, 404)


class SubmitAnswerViewPostTests(ItePrisonerGameViewTestsBase):
    def test_valid_submission_creates_answer_with_graph_data(self):
        self.client.login(username="ipdviewplayer", password="pw")
        response = self.client.post(self.submit_url(), self.valid_post_data())
        self.assertEqual(response.status_code, 200)
        answer = Answer.objects.get(game=self.game, player=self.player)
        self.assertEqual(answer.name, "My Strategy")
        self.assertIsNotNone(answer.graph_json_data)
        self.assertEqual(response.context["submitted_answer"], answer)

    def test_invalid_submission_re_renders_with_errors(self):
        self.client.login(username="ipdviewplayer", password="pw")
        response = self.client.post(
            self.submit_url(), self.valid_post_data(automata="not valid")
        )
        self.assertEqual(response.status_code, 200)
        self.assertFalse(Answer.objects.filter(game=self.game, player=self.player).exists())
        self.assertTrue(response.context["submit_answer_form"].errors)

    def test_management_commands_run_when_flag_enabled(self):
        self.game.run_management_after_submit = True
        self.game.save()
        self.client.login(username="ipdviewplayer", password="pw")
        self.client.post(self.submit_url(), self.valid_post_data())
        answer = Answer.objects.get(game=self.game, player=self.player)
        self.assertTrue(answer.winner)


class ResultsViewTests(ItePrisonerGameViewTestsBase):
    def make_answer(self, name, **overrides):
        user = make_user(name)
        player = make_player(self.session, user, name=name)
        data = dict(
            game=self.game, player=player, automata=ALWAYS_COOPERATE, initial_state="0",
            motivation="m", name=name,
        )
        data.update(overrides)
        return Answer.objects.create(**data)

    def test_hidden_results_block_non_admin(self):
        self.game.results_visible = False
        self.game.save()
        self.client.login(username="ipdviewplayer", password="pw")
        response = self.client.get(self.results_url())
        self.assertEqual(response.status_code, 404)

    def test_no_answers_yet(self):
        self.game.results_visible = True
        self.game.save()
        self.client.login(username="ipdviewplayer", password="pw")
        response = self.client.get(self.results_url())
        self.assertEqual(response.status_code, 200)
        self.assertEqual(len(response.context["answers"]), 0)

    def test_answers_sorted_by_name_and_by_score(self):
        self.game.results_visible = True
        self.game.save()
        self.make_answer("ipdviewzeta", avg_score=1)
        self.make_answer("ipdviewalpha", avg_score=9)
        self.client.login(username="ipdviewplayer", password="pw")
        response = self.client.get(self.results_url())
        self.assertEqual(response.status_code, 200)
        names_alpha_order = [a.name for a in response.context["answers"]]
        self.assertEqual(names_alpha_order, ["ipdviewalpha", "ipdviewzeta"])
        names_score_order = [a.name for a in response.context["answers_sorted_score"]]
        self.assertEqual(names_score_order, ["ipdviewalpha", "ipdviewzeta"])

    def test_display_pairwise_scores_reflects_setting(self):
        self.game.results_visible = True
        self.game.save()
        self.game.itepris_setting.store_scores = False
        self.game.itepris_setting.save()
        self.client.login(username="ipdviewplayer", password="pw")
        response = self.client.get(self.results_url())
        self.assertFalse(response.context["display_pairwise_scores"])
