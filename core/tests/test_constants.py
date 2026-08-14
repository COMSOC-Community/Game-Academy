from types import SimpleNamespace

from django.test import SimpleTestCase

from core import constants


class PlayerUsernameTests(SimpleTestCase):
    def test_includes_session_url_tag_and_player_name(self):
        session = SimpleNamespace(url_tag="mysession")
        self.assertEqual(
            constants.player_username(session, "alice"), "Player_mysession_alice"
        )

    def test_different_sessions_yield_different_usernames(self):
        session_a = SimpleNamespace(url_tag="session-a")
        session_b = SimpleNamespace(url_tag="session-b")
        self.assertNotEqual(
            constants.player_username(session_a, "alice"),
            constants.player_username(session_b, "alice"),
        )


class GuestUsernameTests(SimpleTestCase):
    def test_includes_session_url_tag_and_guest_name(self):
        session = SimpleNamespace(url_tag="mysession")
        self.assertEqual(
            constants.guest_username(session, "bob"), "Guest_mysession_bob"
        )


class GuestPasswordTests(SimpleTestCase):
    def test_prefixes_username(self):
        self.assertEqual(
            constants.guest_password("Guest_mysession_bob"),
            "GuestPass_Guest_mysession_bob",
        )

    def test_accepts_non_string_username(self):
        # guest_password explicitly casts to str, so this should not raise.
        self.assertEqual(constants.guest_password(42), "GuestPass_42")


class TeamPlayerNameTests(SimpleTestCase):
    def test_combines_game_and_team_name(self):
        self.assertEqual(
            constants.team_player_name("Numbers Game", "Team Rocket"),
            "Numbers Game_TeamPlayer_Team Rocket",
        )


class ForbiddenListsTests(SimpleTestCase):
    def test_forbidden_session_url_tags_cover_known_reserved_routes(self):
        for reserved in ("admin", "user", "logout", "createsession"):
            self.assertIn(reserved, constants.FORBIDDEN_SESSION_URL_TAGS)

    def test_forbidden_app_url_tags_cover_known_reserved_routes(self):
        for reserved in ("forcedlogout", "home", "admin"):
            self.assertIn(reserved, constants.FORBIDDEN_APP_URL_TAGS)

    def test_team_user_username_is_forbidden_for_regular_users(self):
        self.assertIn(constants.TEAM_USER_USERNAME, constants.FORBIDDEN_USERNAMES)
