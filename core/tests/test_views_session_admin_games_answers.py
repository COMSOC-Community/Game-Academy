from unittest import mock

from django.conf import settings
from django.test import TestCase
from django.urls import reverse

from core.game_config import INSTALLED_GAMES
from core.random import create_random_players
from core.tests.helpers import make_session, make_user, make_game, make_player
from numbersgame.models import Answer, Setting


class SessionAdminGamesAnswersViewTests(TestCase):
    def setUp(self):
        self.session = make_session("gansweranswers", visible=True)
        self.game = make_game(self.session, url_tag="numb", visible=True)
        Setting.objects.create(game=self.game, lower_bound=0, upper_bound=100)
        self.admin = make_user("ganswersadmin")
        self.session.admins.add(self.admin)

    def url(self):
        return reverse(
            "core:session_admin_games_answers", args=(self.session.url_tag, self.game.url_tag)
        )

    def make_answer(self, name, *, is_random=False, value=42):
        user = make_user(name, is_player=not is_random)
        if is_random:
            user.is_random_player = True
            user.save()
        player = make_player(self.session, user, name=name)
        return Answer.objects.create(
            game=self.game, player=player, answer=value, motivation="m"
        )

    def test_non_admin_is_blocked(self):
        make_user("ganswersintruder")
        self.client.login(username="ganswersintruder", password="pw")
        response = self.client.get(self.url())
        self.assertEqual(response.status_code, 404)

    def test_admin_can_view_with_no_answers(self):
        self.client.login(username="ganswersadmin", password="pw")
        response = self.client.get(self.url())
        self.assertEqual(response.status_code, 200)
        self.assertEqual(list(response.context["answers"]), [])
        self.assertEqual(tuple(response.context["answer_model_fields"]), ("answer", "motivation"))
        self.assertTrue(response.context["export_answers_configured"])
        self.assertIn("random_answers_form", response.context)

    def test_delete_single_answer(self):
        answer = self.make_answer("answerer1")
        player_display_name = answer.player.display_name()
        self.client.login(username="ganswersadmin", password="pw")
        response = self.client.post(
            self.url(), {"delete_answer_form": "1", "remove_answer_id": str(answer.id)}
        )
        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.context["deleted_answer_player"], player_display_name)
        self.assertFalse(Answer.objects.filter(pk=answer.pk).exists())

    def test_delete_all_answers(self):
        self.make_answer("answerer2")
        self.make_answer("answerer3")
        self.client.login(username="ganswersadmin", password="pw")
        response = self.client.post(self.url(), {"delete_all_answers_form": "1"})
        self.assertEqual(response.status_code, 200)
        self.assertTrue(response.context["all_answers_deleted"])
        self.assertEqual(Answer.objects.filter(game=self.game).count(), 0)

    def test_delete_all_random_answers_leaves_regular_ones(self):
        regular = self.make_answer("regularanswerer")
        self.make_answer("randomanswerer", is_random=True)
        self.client.login(username="ganswersadmin", password="pw")
        response = self.client.post(
            self.url(), {"delete_all_random_answers_form": "1"}
        )
        self.assertEqual(response.status_code, 200)
        self.assertTrue(response.context["all_answers_deleted"])
        remaining = Answer.objects.filter(game=self.game)
        self.assertEqual(list(remaining), [regular])

    def test_random_answers_form_generates_answers(self):
        self.client.login(username="ganswersadmin", password="pw")
        response = self.client.post(
            self.url(),
            {"random_answers_form": "1", "num_answers": "3", "run_management": ""},
        )
        self.assertEqual(response.status_code, 200)
        self.assertEqual(Answer.objects.filter(game=self.game).count(), 3)
        self.assertIn("SUCCESS", response.context["random_answers_log"])

    def test_random_answers_form_with_run_management_recomputes_results(self):
        self.client.login(username="ganswersadmin", password="pw")
        response = self.client.post(
            self.url(),
            {"random_answers_form": "1", "num_answers": "2", "run_management": "on"},
        )
        self.assertEqual(response.status_code, 200)
        self.assertIsNotNone(self.game.result_ng)

    def test_random_answers_form_hidden_once_random_player_cap_reached(self):
        from gameserver.local_settings import MAX_NUM_RANDOM_PER_SESSION

        create_random_players(self.session, MAX_NUM_RANDOM_PER_SESSION)
        self.client.login(username="ganswersadmin", password="pw")
        response = self.client.get(self.url())
        self.assertTrue(response.context["max_num_random_players_reached"])
        self.assertNotIn("random_answers_form", response.context)

    def test_answers_export_returns_csv(self):
        self.client.login(username="ganswersadmin", password="pw")
        response = self.client.get(
            reverse(
                "core:session_admin_games_answers_export",
                args=(self.session.url_tag, self.game.url_tag),
            )
        )
        self.assertEqual(response.status_code, 200)
        self.assertEqual(response["Content-Type"], "text/csv")

    def test_answers_export_blocked_for_non_admin(self):
        make_user("ganswersexportintruder")
        self.client.login(username="ganswersexportintruder", password="pw")
        response = self.client.get(
            reverse(
                "core:session_admin_games_answers_export",
                args=(self.session.url_tag, self.game.url_tag),
            )
        )
        self.assertEqual(response.status_code, 404)

    def test_no_answer_model_configured_shows_placeholder(self):
        config = next(c for c in INSTALLED_GAMES if c.name == "numbersgame")
        self.client.login(username="ganswersadmin", password="pw")
        with mock.patch.object(config, "answer_model", None):
            response = self.client.get(self.url())
        self.assertEqual(response.status_code, 200)
        self.assertTrue(response.context["no_answer_model"])
        self.assertNotIn("answers", response.context)

    def test_answer_model_fields_are_auto_derived_when_not_configured(self):
        config = next(c for c in INSTALLED_GAMES if c.name == "numbersgame")
        self.client.login(username="ganswersadmin", password="pw")
        with mock.patch.object(config, "answer_model_fields", None):
            response = self.client.get(self.url())
        self.assertEqual(response.status_code, 200)
        fields = response.context["answer_model_fields"]
        self.assertNotIn("id", fields)
        self.assertNotIn("game", fields)
        self.assertNotIn("player", fields)
        self.assertIn("answer", fields)

    def test_answers_export_404s_when_no_export_function_configured(self):
        config = next(c for c in INSTALLED_GAMES if c.name == "numbersgame")
        self.client.login(username="ganswersadmin", password="pw")
        with mock.patch.object(config, "answer_to_csv_func", None):
            response = self.client.get(
                reverse(
                    "core:session_admin_games_answers_export",
                    args=(self.session.url_tag, self.game.url_tag),
                )
            )
        self.assertEqual(response.status_code, 404)
