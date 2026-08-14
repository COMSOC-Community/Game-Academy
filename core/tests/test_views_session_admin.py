import zipfile
import io

from django.conf import settings
from django.test import TestCase, override_settings
from django.urls import reverse

from core.models import Session
from core.tests.helpers import make_session, make_user, make_player


def valid_create_session_data(**overrides):
    data = {
        "create_session_form": "1",
        "url_tag": "newsession",
        "name": "New Session",
        "long_name": "The New Session",
        "show_guest_login": "on",
        "show_user_login": "on",
        "show_create_account": "on",
        "visible": "on",
    }
    data.update(overrides)
    return data


class CreateSessionViewTests(TestCase):
    def test_anonymous_user_is_blocked(self):
        response = self.client.get(reverse("core:create_session"))
        self.assertEqual(response.status_code, 404)

    def test_player_restricted_user_is_redirected_not_shown_the_form(self):
        session = make_session("playersessioncs", visible=True)
        user = make_user("Player_playersessioncs_pat", is_player=True)
        make_player(session, user, name="pat")
        self.client.login(username="Player_playersessioncs_pat", password="pw")
        response = self.client.get(reverse("core:create_session"))
        self.assertEqual(response.status_code, 302)

    def test_regular_authenticated_user_sees_form(self):
        make_user("creator")
        self.client.login(username="creator", password="pw")
        response = self.client.get(reverse("core:create_session"))
        self.assertEqual(response.status_code, 200)
        self.assertIn("create_session_form", response.context)

    @override_settings(DEBUG=True)
    def test_valid_submission_creates_session_and_makes_creator_admin(self):
        user = make_user("creator2")
        self.client.login(username="creator2", password="pw")
        response = self.client.post(
            reverse("core:create_session"), valid_create_session_data()
        )
        self.assertEqual(response.status_code, 200)
        session = Session.objects.get(url_tag="newsession")
        self.assertIn(user, session.admins.all())
        self.assertIn(user, session.super_admins.all())
        self.assertEqual(response.context["created_session"], session)

    @override_settings(DEBUG=True)
    def test_duplicate_url_tag_shows_error_and_creates_nothing(self):
        make_session("newsession")
        make_user("creator3")
        self.client.login(username="creator3", password="pw")
        response = self.client.post(
            reverse("core:create_session"), valid_create_session_data()
        )
        self.assertEqual(response.status_code, 200)
        self.assertTrue(response.context["create_session_form"].errors)
        self.assertEqual(Session.objects.filter(url_tag="newsession").count(), 1)

    def test_form_hidden_once_max_sessions_reached(self):
        user = make_user("prolificcreator")
        for i in range(settings.MAX_NUM_SESSION_PER_USER):
            s = make_session(f"maxsession{i}")
            s.admins.add(user)
        self.client.login(username="prolificcreator", password="pw")
        response = self.client.get(reverse("core:create_session"))
        self.assertTrue(response.context["max_num_session_reached"])
        self.assertNotIn("create_session_form", response.context)


class SessionAdminSettingsViewTests(TestCase):
    def setUp(self):
        self.session = make_session("adminviewsession", visible=True)
        self.admin = make_user("sessionadmin")
        self.session.admins.add(self.admin)

    def test_non_admin_is_blocked(self):
        make_user("notanadmin")
        self.client.login(username="notanadmin", password="pw")
        response = self.client.get(
            reverse("core:session_admin", args=(self.session.url_tag,))
        )
        self.assertEqual(response.status_code, 404)

    def test_admin_can_view_the_page(self):
        self.client.login(username="sessionadmin", password="pw")
        response = self.client.get(
            reverse("core:session_admin", args=(self.session.url_tag,))
        )
        self.assertEqual(response.status_code, 200)
        self.assertIn("modify_session_form", response.context)
        self.assertIn("delete_session_form", response.context)

    def test_modify_updates_session_fields(self):
        self.client.login(username="sessionadmin", password="pw")
        response = self.client.post(
            reverse("core:session_admin", args=(self.session.url_tag,)),
            {
                "modify_session_form": "1",
                "name": "Renamed Session",
                "long_name": "The Renamed Session",
                "show_guest_login": "on",
                "show_user_login": "on",
                "show_create_account": "on",
                "visible": "on",
                "show_side_panel": "on",
                "show_game_nav_home": "on",
                "show_game_nav_result": "on",
            },
        )
        self.assertEqual(response.status_code, 200)
        self.assertTrue(response.context["session_modified"])
        self.session.refresh_from_db()
        self.assertEqual(self.session.name, "Renamed Session")
        self.assertEqual(self.session.long_name, "The Renamed Session")

    def test_modify_duplicate_name_shows_error_and_does_not_rename(self):
        make_session("othernamedsession", name="Taken Name")
        self.client.login(username="sessionadmin", password="pw")
        response = self.client.post(
            reverse("core:session_admin", args=(self.session.url_tag,)),
            {
                "modify_session_form": "1",
                "name": "Taken Name",
                "long_name": "Whatever Long Name",
                "show_side_panel": "on",
                "show_game_nav_home": "on",
                "show_game_nav_result": "on",
            },
        )
        self.assertEqual(response.status_code, 200)
        self.assertTrue(response.context["modify_session_form"].errors)
        self.session.refresh_from_db()
        self.assertEqual(self.session.name, "adminviewsession")

    def test_delete_with_correct_password_deletes_session(self):
        self.client.login(username="sessionadmin", password="pw")
        response = self.client.post(
            reverse("core:session_admin", args=(self.session.url_tag,)),
            {"delete_session_form": "1", "delete": "on", "password": "pw"},
        )
        self.assertRedirects(response, reverse("core:message"))
        self.assertFalse(Session.objects.filter(pk=self.session.pk).exists())

    def test_delete_with_wrong_password_keeps_session(self):
        self.client.login(username="sessionadmin", password="pw")
        response = self.client.post(
            reverse("core:session_admin", args=(self.session.url_tag,)),
            {"delete_session_form": "1", "delete": "on", "password": "wrongpw"},
        )
        self.assertEqual(response.status_code, 200)
        self.assertTrue(Session.objects.filter(pk=self.session.pk).exists())

    def test_post_without_known_marker_is_404(self):
        self.client.login(username="sessionadmin", password="pw")
        response = self.client.post(
            reverse("core:session_admin", args=(self.session.url_tag,)),
            {"unknown_marker": "1"},
        )
        self.assertEqual(response.status_code, 404)


class SessionExportViewTests(TestCase):
    def setUp(self):
        self.session = make_session("exportsession", visible=True)
        self.admin = make_user("exportadmin")
        self.session.admins.add(self.admin)

    def test_non_admin_is_blocked_from_csv_export(self):
        make_user("exportintruder")
        self.client.login(username="exportintruder", password="pw")
        response = self.client.get(
            reverse("core:session_admin_export", args=(self.session.url_tag,))
        )
        self.assertEqual(response.status_code, 404)

    def test_admin_gets_csv_export(self):
        self.client.login(username="exportadmin", password="pw")
        response = self.client.get(
            reverse("core:session_admin_export", args=(self.session.url_tag,))
        )
        self.assertEqual(response.status_code, 200)
        self.assertEqual(response["Content-Type"], "text/csv")
        self.assertIn("attachment;", response["Content-Disposition"])
        self.assertTrue(response.content)

    def test_admin_gets_full_zip_export(self):
        self.client.login(username="exportadmin", password="pw")
        response = self.client.get(
            reverse("core:session_admin_export_full", args=(self.session.url_tag,))
        )
        self.assertEqual(response.status_code, 200)
        self.assertEqual(response["Content-Type"], "application/zip")
        zf = zipfile.ZipFile(io.BytesIO(response.content))
        self.assertIsNone(zf.testzip())
        names = zf.namelist()
        self.assertTrue(any("parameters" in n for n in names))
        self.assertTrue(any("players" in n for n in names))
        self.assertTrue(any("games" in n for n in names))
