from django.conf import settings
from django.test import TestCase
from django.urls import reverse

from core.models import Game
from core.tests.helpers import make_session, make_user, make_game


def valid_create_game_data(**overrides):
    data = {
        "create_game_form": "1",
        "game_type": "numbersgame",
        "name": "My Numbers Game",
        "url_tag": "numb",
        "visible": "on",
        "playable": "on",
        "results_visible": "on",
        "needs_teams": "",
        "description": "",
    }
    data.update(overrides)
    return data


class SessionAdminGamesViewTests(TestCase):
    def setUp(self):
        self.session = make_session("gamesadminsession", visible=True)
        self.admin = make_user("gamesadmin")
        self.session.admins.add(self.admin)

    def test_non_admin_is_blocked(self):
        make_user("gamesintruder")
        self.client.login(username="gamesintruder", password="pw")
        response = self.client.get(
            reverse("core:session_admin_games", args=(self.session.url_tag,))
        )
        self.assertEqual(response.status_code, 404)

    def test_admin_can_view_with_no_games(self):
        self.client.login(username="gamesadmin", password="pw")
        response = self.client.get(
            reverse("core:session_admin_games", args=(self.session.url_tag,))
        )
        self.assertEqual(response.status_code, 200)
        self.assertEqual(list(response.context["games"]), [])
        self.assertIn("create_game_form", response.context)

    def test_create_game_sets_up_defaults(self):
        self.client.login(username="gamesadmin", password="pw")
        response = self.client.post(
            reverse("core:session_admin_games", args=(self.session.url_tag,)),
            valid_create_game_data(),
        )
        self.assertEqual(response.status_code, 200)
        game = Game.objects.get(session=self.session, url_tag="numb")
        self.assertEqual(response.context["new_game"], game)
        self.assertEqual(game.initial_view, "index")
        self.assertEqual(game.view_after_submit, "index")
        self.assertEqual(game.ordering_priority, 0)
        self.assertTrue(game.illustration_path)
        # A Setting instance should have been bootstrapped for the game.
        self.assertIsNotNone(game.numbers_setting)

    def test_create_game_duplicate_name_shows_error(self):
        make_game(self.session, url_tag="othr", name="My Numbers Game")
        self.client.login(username="gamesadmin", password="pw")
        response = self.client.post(
            reverse("core:session_admin_games", args=(self.session.url_tag,)),
            valid_create_game_data(),
        )
        self.assertEqual(response.status_code, 200)
        self.assertTrue(response.context["create_game_form"].errors)
        self.assertEqual(Game.objects.filter(session=self.session).count(), 1)

    def test_create_game_duplicate_url_tag_shows_error(self):
        make_game(self.session, url_tag="numb", name="Some Other Name")
        self.client.login(username="gamesadmin", password="pw")
        response = self.client.post(
            reverse("core:session_admin_games", args=(self.session.url_tag,)),
            valid_create_game_data(),
        )
        self.assertEqual(response.status_code, 200)
        self.assertTrue(response.context["create_game_form"].errors)
        self.assertEqual(Game.objects.filter(session=self.session).count(), 1)

    def test_second_game_gets_incremented_ordering_priority(self):
        self.client.login(username="gamesadmin", password="pw")
        self.client.post(
            reverse("core:session_admin_games", args=(self.session.url_tag,)),
            valid_create_game_data(url_tag="numb1", name="Game One"),
        )
        self.client.post(
            reverse("core:session_admin_games", args=(self.session.url_tag,)),
            valid_create_game_data(url_tag="numb2", name="Game Two"),
        )
        first = Game.objects.get(session=self.session, url_tag="numb1")
        second = Game.objects.get(session=self.session, url_tag="numb2")
        self.assertEqual(first.ordering_priority, 0)
        self.assertEqual(second.ordering_priority, 1)

    def test_illustration_cycles_for_games_of_the_same_type(self):
        self.client.login(username="gamesadmin", password="pw")
        self.client.post(
            reverse("core:session_admin_games", args=(self.session.url_tag,)),
            valid_create_game_data(url_tag="numb1", name="Game One"),
        )
        self.client.post(
            reverse("core:session_admin_games", args=(self.session.url_tag,)),
            valid_create_game_data(url_tag="numb2", name="Game Two"),
        )
        first = Game.objects.get(session=self.session, url_tag="numb1")
        second = Game.objects.get(session=self.session, url_tag="numb2")
        self.assertNotEqual(first.illustration_path, second.illustration_path)

    def test_delete_single_game(self):
        game = make_game(self.session, url_tag="numb")
        self.client.login(username="gamesadmin", password="pw")
        response = self.client.post(
            reverse("core:session_admin_games", args=(self.session.url_tag,)),
            {"delete_game_form": "1", "remove_game_id": str(game.id)},
        )
        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.context["deleted_game_name"], game.name)
        self.assertFalse(Game.objects.filter(pk=game.pk).exists())

    def test_delete_all_games(self):
        make_game(self.session, url_tag="numb1", name="Game One")
        make_game(self.session, url_tag="numb2", name="Game Two")
        self.client.login(username="gamesadmin", password="pw")
        response = self.client.post(
            reverse("core:session_admin_games", args=(self.session.url_tag,)),
            {"delete_all_games_form": "1"},
        )
        self.assertEqual(response.status_code, 200)
        self.assertTrue(response.context["all_games_deleted"])
        self.assertEqual(Game.objects.filter(session=self.session).count(), 0)

    def test_form_hidden_once_max_games_reached(self):
        for i in range(settings.MAX_NUM_GAMES_PER_SESSION):
            make_game(self.session, url_tag=f"g{i}", name=f"Game {i}")
        self.client.login(username="gamesadmin", password="pw")
        response = self.client.get(
            reverse("core:session_admin_games", args=(self.session.url_tag,))
        )
        self.assertTrue(response.context["max_num_games_reached"])
        self.assertNotIn("create_game_form", response.context)

    def test_admin_gets_games_csv_export(self):
        self.client.login(username="gamesadmin", password="pw")
        response = self.client.get(
            reverse("core:session_admin_games_export", args=(self.session.url_tag,))
        )
        self.assertEqual(response.status_code, 200)
        self.assertEqual(response["Content-Type"], "text/csv")

    def test_non_admin_blocked_from_games_csv_export(self):
        make_user("gamesexportintruder")
        self.client.login(username="gamesexportintruder", password="pw")
        response = self.client.get(
            reverse("core:session_admin_games_export", args=(self.session.url_tag,))
        )
        self.assertEqual(response.status_code, 404)
