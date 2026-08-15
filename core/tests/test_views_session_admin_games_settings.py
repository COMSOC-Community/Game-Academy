from unittest import mock

from django.test import TestCase
from django.urls import reverse

from core.game_config import INSTALLED_GAMES
from core.models import Game
from core.tests.helpers import make_session, make_user, make_game, make_player
from numbersgame.models import Setting, Answer


def valid_modify_game_data(prefix, **overrides):
    data = {
        "modify_game_form": "1",
        f"{prefix}-name": "Renamed Numbers",
        f"{prefix}-url_tag": "numb",
        f"{prefix}-playable": "on",
        f"{prefix}-visible": "on",
        f"{prefix}-results_visible": "on",
        f"{prefix}-needs_teams": "",
        f"{prefix}-description": "A description",
        f"{prefix}-illustration_path": "numbersgame/img/NumbersGame1.png",
        f"{prefix}-ordering_priority": "5",
        f"{prefix}-run_management_after_submit": "",
        f"{prefix}-initial_view": "index",
        f"{prefix}-view_after_submit": "index",
    }
    data.update(overrides)
    return data


class SessionAdminGamesSettingsViewTests(TestCase):
    def setUp(self):
        self.session = make_session("gsettingssession", visible=True)
        self.game = make_game(self.session, url_tag="numb", visible=True)
        self.admin = make_user("gsettingsadmin")
        self.session.admins.add(self.admin)

    def url(self):
        return reverse(
            "core:session_admin_games_settings", args=(self.session.url_tag, self.game.url_tag)
        )

    def test_non_admin_is_blocked(self):
        make_user("gsettingsintruder")
        self.client.login(username="gsettingsintruder", password="pw")
        response = self.client.get(self.url())
        self.assertEqual(response.status_code, 404)

    def test_admin_can_view_without_setting_object(self):
        self.client.login(username="gsettingsadmin", password="pw")
        response = self.client.get(self.url())
        self.assertEqual(response.status_code, 200)
        self.assertIn("modify_game_form", response.context)
        self.assertIsNone(response.context["modify_game_setting_form"])
        self.assertTrue(response.context["export_settings_configured"])

    def test_admin_view_includes_setting_form_when_setting_exists(self):
        Setting.objects.create(game=self.game)
        self.client.login(username="gsettingsadmin", password="pw")
        response = self.client.get(self.url())
        self.assertIsNotNone(response.context["modify_game_setting_form"])

    def test_answers_exist_flag_reflects_submitted_answers(self):
        self.client.login(username="gsettingsadmin", password="pw")
        response = self.client.get(self.url())
        self.assertFalse(response.context["answers_exist"])

        user = make_user("answererforflag")
        player = make_player(self.session, user, name="answererforflag")
        Answer.objects.create(game=self.game, player=player, answer=1, motivation="m")
        response = self.client.get(self.url())
        self.assertTrue(response.context["answers_exist"])

    def test_modify_game_form_updates_the_game(self):
        self.client.login(username="gsettingsadmin", password="pw")
        response = self.client.post(self.url(), valid_modify_game_data("numb"))
        self.assertEqual(response.status_code, 200)
        self.assertTrue(response.context["game_modified"])
        self.game.refresh_from_db()
        self.assertEqual(self.game.name, "Renamed Numbers")
        self.assertEqual(self.game.ordering_priority, 5)
        self.assertEqual(self.game.description, "A description")

    def test_modify_game_form_duplicate_name_shows_error(self):
        make_game(self.session, url_tag="othr", name="Taken Name")
        self.client.login(username="gsettingsadmin", password="pw")
        response = self.client.post(
            self.url(), valid_modify_game_data("numb", **{"numb-name": "Taken Name"})
        )
        self.assertEqual(response.status_code, 200)
        self.assertTrue(response.context["modify_game_form"].errors)
        self.game.refresh_from_db()
        self.assertNotEqual(self.game.name, "Taken Name")

    def test_modify_game_setting_form_updates_the_setting(self):
        Setting.objects.create(game=self.game, lower_bound=0, upper_bound=100)
        self.client.login(username="gsettingsadmin", password="pw")
        response = self.client.post(
            self.url(),
            {
                "modify_game_setting_form": "1",
                "lower_bound": "10",
                "upper_bound": "50",
                "factor": "0.5",
                "factor_display": "1/2",
                "histogram_bin_size": "5",
            },
        )
        self.assertEqual(response.status_code, 200)
        self.assertTrue(response.context["setting_modified"])
        self.game.numbers_setting.refresh_from_db()
        self.assertEqual(self.game.numbers_setting.lower_bound, 10)
        self.assertEqual(self.game.numbers_setting.upper_bound, 50)

    def test_modify_game_setting_form_invalid_bounds_shows_error(self):
        Setting.objects.create(game=self.game, lower_bound=0, upper_bound=100)
        self.client.login(username="gsettingsadmin", password="pw")
        response = self.client.post(
            self.url(),
            {
                "modify_game_setting_form": "1",
                "lower_bound": "100",
                "upper_bound": "0",
                "factor": "0.5",
                "factor_display": "1/2",
                "histogram_bin_size": "5",
            },
        )
        self.assertEqual(response.status_code, 200)
        self.assertTrue(response.context["modify_game_setting_form"].errors)
        self.game.numbers_setting.refresh_from_db()
        self.assertEqual(self.game.numbers_setting.lower_bound, 0)

    def test_settings_export_returns_csv(self):
        Setting.objects.create(game=self.game)
        self.client.login(username="gsettingsadmin", password="pw")
        response = self.client.get(
            reverse(
                "core:session_admin_games_settings_export",
                args=(self.session.url_tag, self.game.url_tag),
            )
        )
        self.assertEqual(response.status_code, 200)
        self.assertEqual(response["Content-Type"], "text/csv")

    def test_settings_export_blocked_for_non_admin(self):
        make_user("gsettingsexportintruder")
        self.client.login(username="gsettingsexportintruder", password="pw")
        response = self.client.get(
            reverse(
                "core:session_admin_games_settings_export",
                args=(self.session.url_tag, self.game.url_tag),
            )
        )
        self.assertEqual(response.status_code, 404)

    def test_settings_export_404s_when_no_export_function_configured(self):
        config = next(c for c in INSTALLED_GAMES if c.name == "numbersgame")
        Setting.objects.create(game=self.game)
        self.client.login(username="gsettingsadmin", password="pw")
        with mock.patch.object(config, "settings_to_csv_func", None):
            response = self.client.get(
                reverse(
                    "core:session_admin_games_settings_export",
                    args=(self.session.url_tag, self.game.url_tag),
                )
            )
        self.assertEqual(response.status_code, 404)
