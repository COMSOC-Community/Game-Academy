from unittest import mock

from django.test import TestCase
from django.urls import reverse

from core.tests.helpers import make_session, make_user, make_game


class GameAdminToggleViewsTests(TestCase):
    def setUp(self):
        self.session = make_session("toggle_session", visible=True)
        self.game = make_game(
            self.session, url_tag="numb", game_type="numbersgame",
            visible=False, playable=False, results_visible=False,
        )
        self.admin = make_user("toggleadmin")
        self.session.admins.add(self.admin)

    def toggle_url(self, name):
        return reverse(f"core:{name}", args=(self.session.url_tag, self.game.url_tag))

    def test_visibility_toggle_flips_flag_and_redirects_to_message(self):
        self.client.login(username="toggleadmin", password="pw")
        response = self.client.get(self.toggle_url("numbers_visibility_toggle"))
        self.assertRedirects(response, reverse("core:message"))
        self.game.refresh_from_db()
        self.assertTrue(self.game.visible)

        response = self.client.get(self.toggle_url("numbers_visibility_toggle"))
        self.game.refresh_from_db()
        self.assertFalse(self.game.visible)

    def test_visibility_toggle_blocked_for_non_admin(self):
        make_user("nonadmintoggle")
        self.client.login(username="nonadmintoggle", password="pw")
        response = self.client.get(self.toggle_url("numbers_visibility_toggle"))
        self.assertEqual(response.status_code, 404)
        self.game.refresh_from_db()
        self.assertFalse(self.game.visible)

    def test_play_toggle_flips_playable(self):
        self.client.login(username="toggleadmin", password="pw")
        self.client.get(self.toggle_url("numbers_play_toggle"))
        self.game.refresh_from_db()
        self.assertTrue(self.game.playable)

        self.client.get(self.toggle_url("numbers_play_toggle"))
        self.game.refresh_from_db()
        self.assertFalse(self.game.playable)

    def test_result_toggle_flips_results_visible(self):
        self.client.login(username="toggleadmin", password="pw")
        self.client.get(self.toggle_url("numbers_result_toggle"))
        self.game.refresh_from_db()
        self.assertTrue(self.game.results_visible)

        self.client.get(self.toggle_url("numbers_result_toggle"))
        self.game.refresh_from_db()
        self.assertFalse(self.game.results_visible)

    def test_toggle_redirects_to_game_index_by_default(self):
        self.client.login(username="toggleadmin", password="pw")
        self.client.get(self.toggle_url("numbers_visibility_toggle"))
        self.assertEqual(
            self.client.session["_message_view_next_url"],
            reverse(
                "numbers_game:index",
                kwargs={"session_url_tag": self.session.url_tag, "game_url_tag": self.game.url_tag},
            ),
        )

    def test_toggle_honours_explicit_next_param(self):
        self.client.login(username="toggleadmin", password="pw")
        self.client.get(self.toggle_url("numbers_visibility_toggle") + "?next=/custom/path/")
        self.assertEqual(
            self.client.session["_message_view_next_url"], "/custom/path/"
        )

    @mock.patch("core.views.management.call_command")
    def test_run_management_runs_the_configured_commands(self, mock_call_command):
        self.client.login(username="toggleadmin", password="pw")
        response = self.client.get(self.toggle_url("numbers_run_management"))
        mock_call_command.assert_called_once_with(
            "numbersgame_results", session=self.session.url_tag, game=self.game.url_tag
        )
        self.assertRedirects(response, reverse("core:message"))

    @mock.patch("core.views.management.call_command")
    def test_run_management_blocked_for_non_admin(self, mock_call_command):
        make_user("nonadminrun")
        self.client.login(username="nonadminrun", password="pw")
        response = self.client.get(self.toggle_url("numbers_run_management"))
        self.assertEqual(response.status_code, 404)
        mock_call_command.assert_not_called()
