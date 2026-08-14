from django.test import TestCase, RequestFactory
from django.contrib.auth.models import AnonymousUser
from django.urls import reverse

from core.middelware import EnforceLoginScopeMiddleware
from core.tests.helpers import make_session, make_user, make_game, make_player


class OpenViewTests(TestCase):
    def test_anonymous_user_can_access_an_open_view(self):
        response = self.client.get(reverse("core:index"))
        self.assertEqual(response.status_code, 200)

    def test_non_player_authenticated_user_can_access_an_open_view(self):
        make_user("alice")
        self.client.login(username="alice", password="pw")
        response = self.client.get(reverse("core:index"))
        self.assertEqual(response.status_code, 200)

    def test_player_user_is_redirected_away_from_an_open_view(self):
        session = make_session("playersession", visible=True)
        user = make_user("Player_playersession_bob", is_player=True)
        make_player(session, user, name="bob")
        self.client.login(username="Player_playersession_bob", password="pw")
        response = self.client.get(reverse("core:index"))
        self.assertEqual(response.status_code, 302)
        self.assertIn(
            reverse("core:force_player_logout", args=(session.url_tag,)),
            response["Location"],
        )


class NonOpenViewAuthenticationTests(TestCase):
    def test_anonymous_user_is_blocked_from_a_non_open_view(self):
        session = make_session("existingsession", visible=True)
        response = self.client.get(reverse("core:session_home", args=(session.url_tag,)))
        self.assertEqual(response.status_code, 404)


class SessionAdminBypassTests(TestCase):
    def test_admin_can_reach_hidden_session_and_invisible_game(self):
        session = make_session("hiddensession", visible=False)
        game = make_game(session, url_tag="numb", visible=False)
        admin = make_user("admin1")
        session.admins.add(admin)
        self.client.login(username="admin1", password="pw")
        response = self.client.get(
            reverse("numbers_game:index", args=(session.url_tag, game.url_tag))
        )
        self.assertEqual(response.status_code, 200)


class VisibleSessionScopeTests(TestCase):
    def setUp(self):
        self.session = make_session("visiblesession", visible=True)

    def test_authenticated_user_with_no_player_profile_is_blocked(self):
        make_user("nobody")
        self.client.login(username="nobody", password="pw")
        response = self.client.get(
            reverse("core:session_home", args=(self.session.url_tag,))
        )
        self.assertEqual(response.status_code, 404)

    def test_authenticated_user_with_player_profile_in_another_session_is_blocked(self):
        other_session = make_session("othervisiblesession", visible=True)
        user = make_user("elsewhere_user")
        make_player(other_session, user, name="elsewhere_user")
        self.client.login(username="elsewhere_user", password="pw")
        response = self.client.get(
            reverse("core:session_home", args=(self.session.url_tag,))
        )
        self.assertEqual(response.status_code, 404)

    def test_authenticated_user_with_player_profile_in_this_session_is_allowed(self):
        user = make_user("in_session_user")
        make_player(self.session, user, name="in_session_user")
        self.client.login(username="in_session_user", password="pw")
        response = self.client.get(
            reverse("core:session_home", args=(self.session.url_tag,))
        )
        self.assertEqual(response.status_code, 200)

    def test_session_open_view_is_reachable_by_non_player_without_profile(self):
        make_user("visitor")
        self.client.login(username="visitor", password="pw")
        response = self.client.get(
            reverse("core:session_portal", args=(self.session.url_tag,))
        )
        self.assertEqual(response.status_code, 200)


class HiddenSessionScopeTests(TestCase):
    def setUp(self):
        self.session = make_session("hiddenscopesession", visible=False)

    def test_own_player_of_hidden_session_is_still_blocked_from_home(self):
        user = make_user("hidden_player", is_player=False)
        make_player(self.session, user, name="hidden_player")
        self.client.login(username="hidden_player", password="pw")
        response = self.client.get(
            reverse("core:session_home", args=(self.session.url_tag,))
        )
        self.assertEqual(response.status_code, 404)

    def test_force_player_logout_is_reachable_even_for_hidden_session(self):
        # This view is globally open, so a non-player user is let through before the
        # session is even resolved.
        make_user("visitor2")
        self.client.login(username="visitor2", password="pw")
        response = self.client.get(
            reverse("core:force_player_logout", args=(self.session.url_tag,))
        )
        self.assertEqual(response.status_code, 200)

    def test_force_player_logout_reachable_by_own_player_of_hidden_session(self):
        user = make_user("Player_hiddenscopesession_carl", is_player=True)
        make_player(self.session, user, name="carl")
        self.client.login(username="Player_hiddenscopesession_carl", password="pw")
        response = self.client.get(
            reverse("core:force_player_logout", args=(self.session.url_tag,))
        )
        self.assertEqual(response.status_code, 200)


class GameVisibilityTests(TestCase):
    def setUp(self):
        self.session = make_session("gamevissession", visible=True)
        self.user = make_user("player_gamevis")
        make_player(self.session, self.user, name="player_gamevis")
        self.client.login(username="player_gamevis", password="pw")

    def test_invisible_game_is_blocked_for_non_admin(self):
        game = make_game(self.session, url_tag="numb", visible=False)
        response = self.client.get(
            reverse("numbers_game:index", args=(self.session.url_tag, game.url_tag))
        )
        self.assertEqual(response.status_code, 404)

    def test_visible_game_is_reachable(self):
        game = make_game(self.session, url_tag="numb", visible=True)
        response = self.client.get(
            reverse("numbers_game:index", args=(self.session.url_tag, game.url_tag))
        )
        self.assertEqual(response.status_code, 200)


class PlayerScopeEnforcementTests(TestCase):
    def test_player_open_view_reachable_regardless_of_session(self):
        session = make_session("logoutsession", visible=True)
        user = make_user("Player_logoutsession_dan", is_player=True)
        make_player(session, user, name="dan")
        self.client.login(username="Player_logoutsession_dan", password="pw")
        response = self.client.get(reverse("core:logout"))
        # core:logout is not in OPEN_VIEWS but its own url is not session-scoped
        # ("logout" is a forbidden session tag), and it is in PLAYER_OPEN_VIEWS, so it
        # should not be blocked by the middleware.
        self.assertNotEqual(response.status_code, 404)

    def test_player_is_redirected_when_visiting_another_session(self):
        own_session = make_session("ownsession", visible=True)
        other_session = make_session("othersession2", visible=True)
        user = make_user("Player_ownsession_erin", is_player=True)
        make_player(own_session, user, name="erin")
        self.client.login(username="Player_ownsession_erin", password="pw")

        response = self.client.get(
            reverse("core:session_home", args=(other_session.url_tag,))
        )
        self.assertEqual(response.status_code, 302)
        self.assertIn(
            reverse("core:force_player_logout", args=(own_session.url_tag,)),
            response["Location"],
        )

    def test_player_is_allowed_within_their_own_session(self):
        session = make_session("ownsession2", visible=True)
        user = make_user("Player_ownsession2_finn", is_player=True)
        make_player(session, user, name="finn")
        self.client.login(username="Player_ownsession2_finn", password="pw")

        response = self.client.get(reverse("core:session_home", args=(session.url_tag,)))
        self.assertEqual(response.status_code, 200)


class RequestCachingTests(TestCase):
    """The middleware caches the session/game it resolves, and the computed admin status,
    directly on the request object so downstream code does not have to re-query them."""

    def setUp(self):
        self.factory = RequestFactory()

    def test_caches_resolved_session_and_admin_status(self):
        session = make_session("cachedsession", visible=True)
        admin = make_user("cachedadmin")
        session.admins.add(admin)

        request = self.factory.get(f"/{session.url_tag}/home/")
        request.user = admin
        EnforceLoginScopeMiddleware._enforce_login_scope(request)

        self.assertEqual(request.resolved_session, session)
        self.assertTrue(request.resolved_session_is_admin)
        self.assertFalse(request.resolved_session_is_super_admin)

    def test_caches_resolved_game(self):
        session = make_session("cachedgamesession", visible=True)
        game = make_game(session, url_tag="numb", visible=True)
        user = make_user("cachedplayer")
        make_player(session, user, name="cachedplayer")

        request = self.factory.get(
            f"/{session.url_tag}/numbers/{game.url_tag}/"
        )
        request.user = user
        EnforceLoginScopeMiddleware._enforce_login_scope(request)

        self.assertEqual(request.resolved_game, game)

    def test_anonymous_request_to_non_session_open_view_does_not_resolve_session(self):
        request = self.factory.get("/")
        request.user = AnonymousUser()
        EnforceLoginScopeMiddleware._enforce_login_scope(request)

        self.assertFalse(hasattr(request, "resolved_session"))
