from django.test import TestCase
from django.urls import reverse

from core.tests.helpers import make_session, make_user, make_player, make_game


class ForcePlayerLogoutViewTests(TestCase):
    def setUp(self):
        self.session = make_session("forcelogoutsession", visible=True)

    def url(self, **query):
        base = reverse("core:force_player_logout", args=(self.session.url_tag,))
        if not query:
            return base
        from urllib.parse import urlencode
        return base + "?" + urlencode(query)

    def test_get_uses_session_home_as_default_back_link(self):
        response = self.client.get(self.url())
        self.assertEqual(response.status_code, 200)
        self.assertEqual(
            response.context["url_back"],
            reverse("core:session_home", args=(self.session.url_tag,)),
        )

    def test_get_honours_prev_query_param(self):
        response = self.client.get(self.url(prev="/custom/prev/"))
        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.context["url_back"], "/custom/prev/")

    def test_get_ignores_unsafe_prev_query_param(self):
        response = self.client.get(self.url(prev="https://evil.example.com/"))
        self.assertEqual(response.status_code, 200)
        self.assertEqual(
            response.context["url_back"],
            reverse("core:session_home", args=(self.session.url_tag,)),
        )

    def test_post_logout_and_continue_without_next_redirects_to_index(self):
        user = make_user("Player_forcelogoutsession_kim", is_player=True)
        make_player(self.session, user, name="kim")
        self.client.login(username="Player_forcelogoutsession_kim", password="pw")
        response = self.client.post(self.url(), {"logout_and_continue": "1"})
        self.assertRedirects(response, reverse("core:index"))
        follow_up = self.client.get(reverse("core:index"))
        self.assertFalse(follow_up.context["user_is_authenticated"])

    def test_post_logout_and_continue_with_next_redirects_there(self):
        user = make_user("Player_forcelogoutsession_lee", is_player=True)
        make_player(self.session, user, name="lee")
        self.client.login(username="Player_forcelogoutsession_lee", password="pw")
        response = self.client.post(
            self.url(next=reverse("core:about")), {"logout_and_continue": "1"}
        )
        self.assertRedirects(response, reverse("core:about"))

    def test_post_logout_and_continue_ignores_unsafe_next(self):
        user = make_user("Player_forcelogoutsession_moe", is_player=True)
        make_player(self.session, user, name="moe")
        self.client.login(username="Player_forcelogoutsession_moe", password="pw")
        response = self.client.post(
            self.url(next="https://evil.example.com/"), {"logout_and_continue": "1"}
        )
        self.assertRedirects(response, reverse("core:index"))

    def test_post_without_known_marker_is_404(self):
        response = self.client.post(self.url(), {"unknown_marker": "1"})
        self.assertEqual(response.status_code, 404)


class MessageViewTests(TestCase):
    def test_defaults_when_no_message_was_queued(self):
        response = self.client.get(reverse("core:message"))
        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.context["message"], "This is the default message")
        self.assertEqual(response.context["next_url"], reverse("core:index"))

    def test_unsafe_queued_next_url_falls_back_to_index(self):
        session = self.client.session
        session["_message_view_next_url"] = "https://evil.example.com/"
        session.save()
        response = self.client.get(reverse("core:message"))
        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.context["next_url"], reverse("core:index"))


class SessionHomeViewTests(TestCase):
    def setUp(self):
        self.session = make_session("homesession", visible=True)
        self.visible_game = make_game(
            self.session, url_tag="numb", name="VisibleGame", visible=True
        )
        self.hidden_game = make_game(
            self.session, url_tag="othr", name="HiddenGame", visible=False
        )
        self.admin = make_user("homeadmin")
        self.session.admins.add(self.admin)

    def url(self):
        return reverse("core:session_home", args=(self.session.url_tag,))

    def test_non_admin_sees_only_visible_games(self):
        user = make_user("Player_homesession_pat", is_player=True)
        make_player(self.session, user, name="pat")
        self.client.login(username="Player_homesession_pat", password="pw")
        response = self.client.get(self.url())
        self.assertEqual(list(response.context["games"]), [self.visible_game])
        self.assertNotIn("invisible_games", response.context)

    def test_admin_also_sees_invisible_games_separately(self):
        self.client.login(username="homeadmin", password="pw")
        response = self.client.get(self.url())
        self.assertEqual(list(response.context["games"]), [self.visible_game])
        self.assertEqual(list(response.context["invisible_games"]), [self.hidden_game])
