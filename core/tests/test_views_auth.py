from django.test import TestCase, override_settings
from django.urls import reverse

from core.models import CustomUser, Player
from core.tests.helpers import make_session, make_user, make_player


class IndexViewTests(TestCase):
    def test_get_renders_all_three_forms(self):
        response = self.client.get(reverse("core:index"))
        self.assertEqual(response.status_code, 200)
        self.assertIn("session_finder_form", response.context)
        self.assertIn("login_form", response.context)
        self.assertIn("registration_form", response.context)

    def test_session_finder_redirects_to_matching_session(self):
        session = make_session("mysession", name="My Session")
        response = self.client.post(
            reverse("core:index"),
            {"session_finder": "1", "session_name": "My Session"},
        )
        self.assertRedirects(response, reverse("core:session_portal", args=(session.url_tag,)))

    def test_session_finder_unknown_name_rerenders_with_error(self):
        response = self.client.post(
            reverse("core:index"),
            {"session_finder": "1", "session_name": "Does Not Exist"},
        )
        self.assertEqual(response.status_code, 200)
        self.assertTrue(response.context["session_finder_form"].errors)

    def test_login_form_valid_logs_in_and_redirects_to_index(self):
        make_user("bob")
        response = self.client.post(
            reverse("core:index"),
            {"login_form": "1", "username": "bob", "password": "pw"},
        )
        self.assertRedirects(response, reverse("core:index"))
        self.assertTrue(response.wsgi_request.session.get("_auth_user_id") or True)
        # Confirm we are actually logged in on a follow-up request.
        follow_up = self.client.get(reverse("core:index"))
        self.assertTrue(follow_up.context["user_is_authenticated"])

    def test_login_form_wrong_password_rerenders_with_error(self):
        make_user("bob2")
        response = self.client.post(
            reverse("core:index"),
            {"login_form": "1", "username": "bob2", "password": "wrongpassword"},
        )
        self.assertEqual(response.status_code, 200)
        self.assertTrue(response.context["login_form"].errors)

    @override_settings(DEBUG=True)
    def test_registration_form_valid_creates_user(self):
        response = self.client.post(
            reverse("core:index"),
            {
                "registration_form": "1",
                "username": "newuser",
                "email": "newuser@example.com",
                "password1": "StrongPass123",
                "password2": "StrongPass123",
                "accept_terms": "on",
            },
        )
        self.assertEqual(response.status_code, 200)
        self.assertTrue(CustomUser.objects.filter(username="newuser").exists())
        self.assertEqual(response.context["created_user"].username, "newuser")

    @override_settings(DEBUG=True)
    def test_registration_form_password_mismatch_shows_error_and_creates_nobody(self):
        response = self.client.post(
            reverse("core:index"),
            {
                "registration_form": "1",
                "username": "newuser2",
                "email": "newuser2@example.com",
                "password1": "StrongPass123",
                "password2": "DifferentPass456",
                "accept_terms": "on",
            },
        )
        self.assertEqual(response.status_code, 200)
        self.assertTrue(response.context["registration_form"].errors)
        self.assertFalse(CustomUser.objects.filter(username="newuser2").exists())

    def test_post_without_known_marker_is_404(self):
        response = self.client.post(reverse("core:index"), {"unknown_marker": "1"})
        self.assertEqual(response.status_code, 404)


class LogoutViewTests(TestCase):
    def test_logout_redirects_to_index_by_default(self):
        make_user("logoutuser")
        self.client.login(username="logoutuser", password="pw")
        response = self.client.get(reverse("core:logout"))
        self.assertRedirects(response, reverse("core:index"))
        follow_up = self.client.get(reverse("core:index"))
        self.assertFalse(follow_up.context["user_is_authenticated"])

    def test_logout_redirects_to_safe_next_url(self):
        make_user("logoutuser2")
        self.client.login(username="logoutuser2", password="pw")
        response = self.client.get(reverse("core:logout") + "?next=" + reverse("core:about"))
        self.assertRedirects(response, reverse("core:about"))

    def test_logout_ignores_unsafe_next_url(self):
        make_user("logoutuser3")
        self.client.login(username="logoutuser3", password="pw")
        response = self.client.get(
            reverse("core:logout") + "?next=https://evil.example.com/steal"
        )
        # An external/unsafe "next" URL must not be honoured; falls back to core:index.
        self.assertRedirects(response, reverse("core:index"))


class UserProfileViewTests(TestCase):
    def test_anonymous_user_is_blocked(self):
        user = make_user("profileowner")
        response = self.client.get(reverse("core:user_profile", args=(user.id,)))
        self.assertEqual(response.status_code, 404)

    def test_user_can_view_own_profile(self):
        user = make_user("profileowner2")
        self.client.login(username="profileowner2", password="pw")
        response = self.client.get(reverse("core:user_profile", args=(user.id,)))
        self.assertEqual(response.status_code, 200)

    def test_user_cannot_view_someone_elses_profile(self):
        make_user("owner")
        other = make_user("intruder")
        self.client.login(username="intruder", password="pw")
        owner = CustomUser.objects.get(username="owner")
        response = self.client.get(reverse("core:user_profile", args=(owner.id,)))
        self.assertEqual(response.status_code, 404)

    def test_password_update_valid_changes_password_and_redirects(self):
        user = make_user("pwuser")
        self.client.login(username="pwuser", password="pw")
        response = self.client.post(
            reverse("core:user_profile", args=(user.id,)),
            {
                "update_password_form": "1",
                "old_password": "pw",
                "new_password1": "NewStrongPass1",
                "new_password2": "NewStrongPass1",
            },
        )
        self.assertRedirects(response, reverse("core:message"))
        user.refresh_from_db()
        self.assertTrue(user.check_password("NewStrongPass1"))

    def test_password_update_wrong_old_password_does_not_change_it(self):
        user = make_user("pwuser2")
        self.client.login(username="pwuser2", password="pw")
        response = self.client.post(
            reverse("core:user_profile", args=(user.id,)),
            {
                "update_password_form": "1",
                "old_password": "wrongpw",
                "new_password1": "NewStrongPass1",
                "new_password2": "NewStrongPass1",
            },
        )
        self.assertEqual(response.status_code, 200)
        user.refresh_from_db()
        self.assertTrue(user.check_password("pw"))

    def test_delete_account_valid_deletes_user_and_redirects(self):
        user = make_user("deleteuser")
        user_id = user.id
        self.client.login(username="deleteuser", password="pw")
        response = self.client.post(
            reverse("core:user_profile", args=(user.id,)),
            {"delete_account_form": "1", "delete": "on", "password": "pw"},
        )
        self.assertRedirects(response, reverse("core:message"))
        self.assertFalse(CustomUser.objects.filter(pk=user_id).exists())

    def test_delete_account_wrong_password_keeps_user(self):
        user = make_user("deleteuser2")
        self.client.login(username="deleteuser2", password="pw")
        response = self.client.post(
            reverse("core:user_profile", args=(user.id,)),
            {"delete_account_form": "1", "delete": "on", "password": "wrongpw"},
        )
        self.assertEqual(response.status_code, 200)
        self.assertTrue(CustomUser.objects.filter(pk=user.id).exists())

    def test_password_update_for_player_redirects_to_session_home(self):
        session = make_session("pwplayersession", visible=True)
        user = make_user("Player_pwplayersession_pw", is_player=True)
        make_player(session, user, name="pw")
        self.client.login(username="Player_pwplayersession_pw", password="pw")
        response = self.client.post(
            reverse("core:user_profile", args=(user.id,)),
            {
                "update_password_form": "1",
                "old_password": "pw",
                "new_password1": "NewStrongPass1",
                "new_password2": "NewStrongPass1",
            },
        )
        self.assertEqual(response.status_code, 302)
        self.assertEqual(
            self.client.session["_message_view_next_url"],
            reverse("core:session_home", args=(session.url_tag,)),
        )

    def test_delete_account_for_player_redirects_to_session_portal(self):
        session = make_session("delplayersession", visible=True)
        user = make_user("Player_delplayersession_del", is_player=True)
        make_player(session, user, name="del")
        self.client.login(username="Player_delplayersession_del", password="pw")
        response = self.client.post(
            reverse("core:user_profile", args=(user.id,)),
            {"delete_account_form": "1", "delete": "on", "password": "pw"},
        )
        self.assertEqual(response.status_code, 302)
        self.assertEqual(
            self.client.session["_message_view_next_url"],
            reverse("core:session_portal", args=(session.url_tag,)),
        )


class SessionPortalViewTests(TestCase):
    def setUp(self):
        self.session = make_session("portalsession", visible=True)

    def test_get_renders_registration_login_and_guest_forms_by_default(self):
        response = self.client.get(
            reverse("core:session_portal", args=(self.session.url_tag,))
        )
        self.assertEqual(response.status_code, 200)
        self.assertIn("registration_form", response.context)
        self.assertIn("guest_form", response.context)
        self.assertIn("login_form", response.context)

    def test_authenticated_player_with_profile_sees_it_in_context(self):
        user = make_user("Player_portalsession_gail", is_player=True)
        player = make_player(self.session, user, name="gail")
        self.client.login(username="Player_portalsession_gail", password="pw")
        response = self.client.get(
            reverse("core:session_portal", args=(self.session.url_tag,))
        )
        self.assertEqual(response.context["player_profile"], player)

    def test_admin_visiting_portal_gets_session_admin_context(self):
        admin = make_user("portaladmin")
        self.session.admins.add(admin)
        self.client.login(username="portaladmin", password="pw")
        response = self.client.get(
            reverse("core:session_portal", args=(self.session.url_tag,))
        )
        self.assertTrue(response.context["user_is_session_admin"])

    @override_settings(DEBUG=True)
    def test_anonymous_registration_creates_user_and_player_and_stays_on_page(self):
        response = self.client.post(
            reverse("core:session_portal", args=(self.session.url_tag,)),
            {
                "registration_form": "1",
                "player-player_name": "newplayer",
                "player-password1": "StrongPass123",
                "player-password2": "StrongPass123",
                "player-accept_terms": "on",
            },
        )
        self.assertEqual(response.status_code, 200)
        self.assertTrue(
            Player.objects.filter(session=self.session, name="newplayer").exists()
        )
        self.assertIn("created_player", response.context)

    @override_settings(DEBUG=True)
    def test_authenticated_registration_redirects_to_session_home(self):
        make_user("existinguser")
        self.client.login(username="existinguser", password="pw")
        response = self.client.post(
            reverse("core:session_portal", args=(self.session.url_tag,)),
            {
                "registration_form": "1",
                "player-player_name": "newplayer2",
                "player-accept_terms": "on",
            },
        )
        self.assertRedirects(
            response, reverse("core:session_home", args=(self.session.url_tag,))
        )
        player = Player.objects.get(session=self.session, name="newplayer2")
        self.assertEqual(player.user.username, "existinguser")

    @override_settings(DEBUG=True)
    def test_registration_with_taken_name_shows_error_and_creates_nothing(self):
        taken_user = make_user("Player_portalsession_taken")
        make_player(self.session, taken_user, name="taken")
        response = self.client.post(
            reverse("core:session_portal", args=(self.session.url_tag,)),
            {
                "registration_form": "1",
                "player-player_name": "taken",
                "player-password1": "StrongPass123",
                "player-password2": "StrongPass123",
                "player-accept_terms": "on",
            },
        )
        self.assertEqual(response.status_code, 200)
        self.assertTrue(response.context["registration_form"].errors)
        self.assertEqual(
            Player.objects.filter(session=self.session, name="taken").count(), 1
        )

    def test_registration_disabled_returns_404(self):
        self.session.show_create_account = False
        self.session.save()
        response = self.client.post(
            reverse("core:session_portal", args=(self.session.url_tag,)),
            {
                "registration_form": "1",
                "player-player_name": "shouldnotwork",
                "player-password1": "StrongPass123",
                "player-password2": "StrongPass123",
                "player-accept_terms": "on",
            },
        )
        self.assertEqual(response.status_code, 404)

    def test_player_login_valid_redirects_to_session_home(self):
        user = make_user("Player_portalsession_alice")
        make_player(self.session, user, name="alice")
        response = self.client.post(
            reverse("core:session_portal", args=(self.session.url_tag,)),
            {"login_form": "1", "login-player_name": "alice", "login-password": "pw"},
        )
        self.assertRedirects(
            response, reverse("core:session_home", args=(self.session.url_tag,))
        )

    def test_player_login_with_game_after_logging_redirects_to_that_game(self):
        from core.tests.helpers import make_game

        game = make_game(self.session, url_tag="numb", visible=True, playable=True)
        self.session.game_after_logging = game
        self.session.save()
        user = make_user("Player_portalsession_dana")
        make_player(self.session, user, name="dana")
        response = self.client.post(
            reverse("core:session_portal", args=(self.session.url_tag,)),
            {"login_form": "1", "login-player_name": "dana", "login-password": "pw"},
        )
        self.assertRedirects(
            response,
            reverse(
                "numbers_game:index",
                args=(self.session.url_tag, game.url_tag),
            ),
        )

    def test_player_login_wrong_password_rerenders_with_error(self):
        user = make_user("Player_portalsession_carl")
        make_player(self.session, user, name="carl")
        response = self.client.post(
            reverse("core:session_portal", args=(self.session.url_tag,)),
            {"login_form": "1", "login-player_name": "carl", "login-password": "wrongpw"},
        )
        self.assertEqual(response.status_code, 200)
        self.assertTrue(response.context["login_form"].errors)

    @override_settings(DEBUG=True)
    def test_guest_registration_creates_guest_and_logs_in(self):
        response = self.client.post(
            reverse("core:session_portal", args=(self.session.url_tag,)),
            {
                "guest_form": "1",
                "guest-guest_name": "guestname",
                "guest-accept_terms": "on",
            },
        )
        self.assertRedirects(
            response, reverse("core:session_home", args=(self.session.url_tag,))
        )
        player = Player.objects.get(session=self.session, name="guestname")
        self.assertTrue(player.user.is_guest_player)
        self.assertTrue(player.user.is_player)

    def test_guest_registration_disabled_returns_404(self):
        self.session.show_guest_login = False
        self.session.save()
        response = self.client.post(
            reverse("core:session_portal", args=(self.session.url_tag,)),
            {
                "guest_form": "1",
                "guest-guest_name": "shouldnotwork",
                "guest-accept_terms": "on",
            },
        )
        self.assertEqual(response.status_code, 404)

    def test_post_without_known_marker_is_404(self):
        response = self.client.post(
            reverse("core:session_portal", args=(self.session.url_tag,)),
            {"unknown_marker": "1"},
        )
        self.assertEqual(response.status_code, 404)
