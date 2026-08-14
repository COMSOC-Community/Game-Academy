from django.contrib.auth.models import AnonymousUser
from django.test import TestCase, RequestFactory
from django.urls import reverse

from core.models import Team
from core.views import (
    base_context_initialiser,
    session_context_initialiser,
    game_context_initialiser,
)
from core.tests.helpers import make_session, make_user, make_game, make_player
from numbersgame.models import Answer


class ContextInitialiserTestsBase(TestCase):
    def setUp(self):
        self.factory = RequestFactory()

    def build_request(self, user=None):
        request = self.factory.get("/irrelevant/")
        request.user = user if user is not None else AnonymousUser()
        return request


class BaseContextInitialiserTests(ContextInitialiserTestsBase):
    def test_anonymous_user_is_marked_unauthenticated(self):
        context = base_context_initialiser(self.build_request())
        self.assertFalse(context["user_is_authenticated"])
        self.assertFalse(context["show_side_panel"])
        self.assertNotIn("user", context)

    def test_authenticated_regular_user(self):
        user = make_user("alice")
        context = base_context_initialiser(self.build_request(user))
        self.assertTrue(context["user_is_authenticated"])
        self.assertTrue(context["show_side_panel"])
        self.assertEqual(context["user"], user)
        self.assertFalse(context["user_is_only_player"])
        self.assertFalse(context["user_is_only_guest"])
        self.assertEqual(list(context["user_administrated_sessions"]), [])
        self.assertEqual(context["user_player_sessions"], [])

    def test_administrated_sessions_are_listed(self):
        user = make_user("adminuser")
        session = make_session("adminsession")
        session.admins.add(user)
        context = base_context_initialiser(self.build_request(user))
        self.assertIn(session, context["user_administrated_sessions"])

    def test_player_sessions_exclude_administrated_ones(self):
        user = make_user("multiuser")
        admin_session = make_session("admsession")
        player_session = make_session("plysession")
        admin_session.admins.add(user)
        make_player(admin_session, user, name="multiuser")
        make_player(player_session, user, name="multiuser")
        context = base_context_initialiser(self.build_request(user))
        self.assertIn(admin_session, context["user_administrated_sessions"])
        self.assertEqual(context["user_player_sessions"], [player_session])

    def test_player_restricted_user_has_no_admin_or_player_session_lists(self):
        session = make_session("restrictedsession")
        user = make_user("Player_restrictedsession_bob", is_player=True)
        make_player(session, user, name="bob")
        context = base_context_initialiser(self.build_request(user))
        self.assertTrue(context["user_is_only_player"])
        self.assertNotIn("user_administrated_sessions", context)
        self.assertNotIn("user_player_sessions", context)

    def test_guest_flag_is_propagated(self):
        user = make_user("guestuser")
        user.is_guest_player = True
        user.save()
        context = base_context_initialiser(self.build_request(user))
        self.assertTrue(context["user_is_only_guest"])

    def test_extends_and_returns_the_same_context_object_passed_in(self):
        preexisting = {"custom_key": "custom_value"}
        context = base_context_initialiser(self.build_request(), preexisting)
        self.assertIs(context, preexisting)
        self.assertEqual(context["custom_key"], "custom_value")
        self.assertIn("user_is_authenticated", context)


class SessionContextInitialiserTests(ContextInitialiserTestsBase):
    def setUp(self):
        super().setUp()
        self.session = make_session("scisession")

    def test_sets_session_in_context(self):
        context = session_context_initialiser(self.build_request(), self.session)
        self.assertEqual(context["session"], self.session)

    def test_anonymous_user_gets_no_admin_status_keys(self):
        context = session_context_initialiser(self.build_request(), self.session)
        self.assertNotIn("user_is_session_admin", context)
        self.assertNotIn("user_is_session_super_admin", context)

    def test_regular_authenticated_user_is_not_admin(self):
        user = make_user("regular")
        context = session_context_initialiser(self.build_request(user), self.session)
        self.assertFalse(context["user_is_session_admin"])
        self.assertFalse(context["user_is_session_super_admin"])

    def test_admin_user_is_flagged_admin_but_not_super_admin(self):
        admin = make_user("theadmin")
        self.session.admins.add(admin)
        context = session_context_initialiser(self.build_request(admin), self.session)
        self.assertTrue(context["user_is_session_admin"])
        self.assertFalse(context["user_is_session_super_admin"])

    def test_uses_cached_admin_status_from_request_when_available(self):
        user = make_user("notreallyadmin")
        request = self.build_request(user)
        # This user is not actually in session.admins, but the middleware would already
        # have computed and cached the status on the request; the function must trust it
        # rather than re-querying.
        request.resolved_session = self.session
        request.resolved_session_is_admin = True
        request.resolved_session_is_super_admin = True
        context = session_context_initialiser(request, self.session)
        self.assertTrue(context["user_is_session_admin"])
        self.assertTrue(context["user_is_session_super_admin"])

    def test_ignores_cached_admin_status_computed_for_a_different_session(self):
        other_session = make_session("otherscisession")
        user = make_user("mismatcheduser")
        request = self.build_request(user)
        request.resolved_session = other_session
        request.resolved_session_is_admin = True
        request.resolved_session_is_super_admin = True
        context = session_context_initialiser(request, self.session)
        # Falls back to a fresh, correct computation for `self.session`: the user is not
        # an admin there, regardless of the mismatched cached value.
        self.assertFalse(context["user_is_session_admin"])

    def test_side_panel_hidden_for_non_admin_when_session_hides_it(self):
        self.session.show_side_panel = False
        self.session.save()
        user = make_user("nonadmin2")
        context = session_context_initialiser(self.build_request(user), self.session)
        self.assertFalse(context["show_side_panel"])
        self.assertEqual(
            context["session_portal_url"],
            reverse("core:session_portal", args=(self.session.url_tag,)),
        )

    def test_side_panel_not_forced_hidden_for_admin(self):
        self.session.show_side_panel = False
        self.session.save()
        admin = make_user("panelAdmin")
        self.session.admins.add(admin)
        context = session_context_initialiser(self.build_request(admin), self.session)
        self.assertNotIn("show_side_panel", context)

    def test_side_panel_untouched_when_session_shows_it(self):
        context = session_context_initialiser(
            self.build_request(make_user("someone")), self.session
        )
        self.assertNotIn("show_side_panel", context)


class GameContextInitialiserTests(ContextInitialiserTestsBase):
    def setUp(self):
        super().setUp()
        self.session = make_session("gcisession")
        self.game = make_game(self.session, url_tag="numb")
        self.user = make_user("gciuser")

    def call(self, user, *, admin=False):
        context = {"user_is_session_admin": admin}
        request = self.build_request(user)
        return game_context_initialiser(request, self.session, self.game, Answer, context)

    def test_no_player_profile_means_no_player_team_or_answer(self):
        context = self.call(self.user)
        self.assertIsNone(context["player"])
        self.assertIsNone(context["team"])
        self.assertIsNone(context["answer"])
        self.assertIsNone(context["submitting_player"])

    def test_player_without_answer(self):
        player = make_player(self.session, self.user, name="gciuser")
        context = self.call(self.user)
        self.assertEqual(context["player"], player)
        self.assertIsNone(context["answer"])
        self.assertEqual(context["submitting_player"], player)
        self.assertTrue(context["game_nav_display_answer"])

    def test_player_with_answer(self):
        player = make_player(self.session, self.user, name="gciuser")
        answer = Answer.objects.create(game=self.game, player=player, answer=42)
        context = self.call(self.user)
        self.assertEqual(context["answer"], answer)
        self.assertFalse(context["game_nav_display_answer"])

    def test_needs_teams_without_a_team_yet(self):
        self.game.needs_teams = True
        self.game.save()
        make_player(self.session, self.user, name="gciuser")
        context = self.call(self.user)
        self.assertIsNone(context["team"])
        self.assertIsNone(context["submitting_player"])
        self.assertTrue(context["game_nav_display_team"])
        self.assertFalse(context["game_nav_display_answer"])

    def test_needs_teams_with_a_team_and_answer(self):
        self.game.needs_teams = True
        self.game.save()
        player = make_player(self.session, self.user, name="gciuser")
        team_user = make_user("TeamUser_gci")
        team_player = make_player(self.session, team_user, name="teamplayer_gci", is_team_player=True)
        team = Team.objects.create(
            name="Team A", game=self.game, creator=player, team_player=team_player,
        )
        team.players.add(player)
        answer = Answer.objects.create(game=self.game, player=team_player, answer=7)

        context = self.call(self.user)
        self.assertEqual(context["team"], team)
        self.assertEqual(context["submitting_player"], team_player)
        self.assertEqual(context["answer"], answer)
        self.assertFalse(context["game_nav_display_team"])
        self.assertFalse(context["game_nav_display_answer"])

    def test_non_admin_context_has_no_counts(self):
        context = self.call(self.user, admin=False)
        self.assertNotIn("num_players", context)
        self.assertNotIn("num_received_answers", context)

    def test_admin_context_includes_counts(self):
        player1 = make_player(self.session, self.user, name="gciuser")
        Answer.objects.create(game=self.game, player=player1, answer=1)
        other_user = make_user("gciuser2")
        make_player(self.session, other_user, name="gciuser2")

        admin = make_user("gciadmin")
        context = self.call(admin, admin=True)
        self.assertEqual(context["num_players"], 2)
        self.assertEqual(context["num_received_answers"], 1)
        self.assertEqual(context["percent_answer_received"], 50)

    def test_admin_context_percent_is_zero_with_no_players(self):
        admin = make_user("gciadmin2")
        context = self.call(admin, admin=True)
        self.assertEqual(context["num_players"], 0)
        self.assertEqual(context["percent_answer_received"], 0)

    def test_admin_context_includes_team_counts_when_game_needs_teams(self):
        self.game.needs_teams = True
        self.game.save()
        player = make_player(self.session, self.user, name="gciuser")
        team_user = make_user("TeamUser_gci2")
        team_player = make_player(self.session, team_user, name="teamplayer_gci2", is_team_player=True)
        team = Team.objects.create(
            name="Team B", game=self.game, creator=player, team_player=team_player,
        )
        team.players.add(player)
        Answer.objects.create(game=self.game, player=team_player, answer=3)

        admin = make_user("gciadmin3")
        context = self.call(admin, admin=True)
        self.assertEqual(context["num_teams"], 1)
        self.assertEqual(context["num_received_answers"], 1)
        self.assertEqual(context["percent_answer_received"], 100)

    def test_requires_user_is_session_admin_key_to_already_be_set(self):
        # game_context_initialiser is documented to run after session_context_initialiser,
        # which is what populates this key; calling it directly without that key is a
        # programming error and should fail loudly rather than silently.
        request = self.build_request(self.user)
        with self.assertRaises(KeyError):
            game_context_initialiser(request, self.session, self.game, Answer, {})
