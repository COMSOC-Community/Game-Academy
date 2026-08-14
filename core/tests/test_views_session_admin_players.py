from django.core.files.uploadedfile import SimpleUploadedFile
from django.test import TestCase, override_settings
from django.urls import reverse

from core.models import CustomUser, Player
from core.random import create_random_players
from core.tests.helpers import make_session, make_user, make_player


class SessionAdminPlayersViewTests(TestCase):
    def setUp(self):
        self.session = make_session("playersadminsession", visible=True)
        self.admin = make_user("playersadmin")
        self.session.admins.add(self.admin)

    def url(self):
        return reverse("core:session_admin_players", args=(self.session.url_tag,))

    def test_non_admin_is_blocked(self):
        make_user("playersintruder")
        self.client.login(username="playersintruder", password="pw")
        response = self.client.get(self.url())
        self.assertEqual(response.status_code, 404)

    def test_admin_can_view_with_no_players(self):
        self.client.login(username="playersadmin", password="pw")
        response = self.client.get(self.url())
        self.assertEqual(response.status_code, 200)
        self.assertEqual(list(response.context["players"]), [])
        self.assertEqual(list(response.context["guests"]), [])
        self.assertIn("add_player_form", response.context)

    @override_settings(DEBUG=True)
    def test_add_player_valid_creates_user_and_player(self):
        self.client.login(username="playersadmin", password="pw")
        response = self.client.post(
            self.url(),
            {
                "add_player_form": "1",
                "player_name": "newplayer",
                "password1": "StrongPass123",
                "password2": "StrongPass123",
                "accept_terms": "on",
            },
        )
        self.assertEqual(response.status_code, 200)
        player = Player.objects.get(session=self.session, name="newplayer")
        self.assertEqual(response.context["new_player"], player)
        self.assertTrue(player.user.is_player)

    @override_settings(DEBUG=True)
    def test_add_player_duplicate_name_shows_error(self):
        existing_user = make_user("Player_playersadminsession_taken")
        make_player(self.session, existing_user, name="taken")
        self.client.login(username="playersadmin", password="pw")
        response = self.client.post(
            self.url(),
            {
                "add_player_form": "1",
                "player_name": "taken",
                "password1": "StrongPass123",
                "password2": "StrongPass123",
                "accept_terms": "on",
            },
        )
        self.assertEqual(response.status_code, 200)
        self.assertTrue(response.context["add_player_form"].errors)
        self.assertEqual(
            Player.objects.filter(session=self.session, name="taken").count(), 1
        )

    def test_random_players_form_creates_random_players(self):
        self.client.login(username="playersadmin", password="pw")
        response = self.client.post(
            self.url(), {"random_players_form": "1", "num_players": "3"}
        )
        self.assertEqual(response.status_code, 200)
        self.assertEqual(
            Player.objects.filter(
                session=self.session, user__is_random_player=True
            ).count(),
            3,
        )
        self.assertIn("populated", response.context["random_players_log"])

    def test_random_players_form_hidden_once_cap_reached(self):
        # Bulk-create up to the MAX_NUM_RANDOM_PER_SESSION cap using the app's own helper,
        # to exercise the real gating logic without a slow per-request loop.
        from gameserver.local_settings import MAX_NUM_RANDOM_PER_SESSION

        create_random_players(self.session, MAX_NUM_RANDOM_PER_SESSION)
        self.client.login(username="playersadmin", password="pw")
        response = self.client.get(self.url())
        self.assertTrue(response.context["max_num_random_players_reached"])
        self.assertNotIn("random_players_form", response.context)

    def test_import_csv_valid_creates_players(self):
        self.client.login(username="playersadmin", password="pw")
        csv_content = b"username,password\nalice,StrongPass123\nbob,StrongPass456\n"
        csv_file = SimpleUploadedFile("players.csv", csv_content, content_type="text/csv")
        response = self.client.post(
            self.url(),
            {"import_player_csv_form": "1", "csv_file": csv_file},
        )
        self.assertEqual(response.status_code, 200)
        self.assertEqual(
            Player.objects.filter(session=self.session, name__in=["alice", "bob"]).count(),
            2,
        )
        self.assertIn("2 players imported", response.context["import_player_csv_log"])

    def test_import_csv_wrong_extension_shows_error(self):
        self.client.login(username="playersadmin", password="pw")
        txt_file = SimpleUploadedFile("players.txt", b"not,a,csv", content_type="text/plain")
        response = self.client.post(
            self.url(),
            {"import_player_csv_form": "1", "csv_file": txt_file},
        )
        self.assertEqual(response.status_code, 200)
        self.assertTrue(response.context["import_player_csv_form"].errors)
        self.assertEqual(Player.objects.filter(session=self.session).count(), 0)

    def test_delete_player_removes_user_and_player(self):
        user = make_user("Player_playersadminsession_pat", is_player=True)
        player = make_player(self.session, user, name="pat")
        self.client.login(username="playersadmin", password="pw")
        response = self.client.post(
            self.url(),
            {"delete_player_form": "1", "remove_player_id": str(player.id)},
        )
        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.context["deleted_player_name"], "pat")
        self.assertFalse(Player.objects.filter(pk=player.pk).exists())
        self.assertFalse(CustomUser.objects.filter(pk=user.pk).exists())

    def test_delete_guest_uses_guest_context_key(self):
        guest_user = make_user("Guest_playersadminsession_gina", is_player=True)
        guest_user.is_guest_player = True
        guest_user.save()
        guest_player = make_player(self.session, guest_user, name="gina")
        self.client.login(username="playersadmin", password="pw")
        response = self.client.post(
            self.url(),
            {"delete_guest_form": "1", "remove_player_id": str(guest_player.id)},
        )
        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.context["deleted_guest_name"], "gina")
        self.assertFalse(Player.objects.filter(pk=guest_player.pk).exists())

    def test_delete_all_players_leaves_guests_untouched(self):
        u1 = make_user("Player_playersadminsession_p1", is_player=True)
        u2 = make_user("Player_playersadminsession_p2", is_player=True)
        make_player(self.session, u1, name="p1")
        make_player(self.session, u2, name="p2")
        guest_user = make_user("Guest_playersadminsession_g1", is_player=True)
        guest_user.is_guest_player = True
        guest_user.save()
        make_player(self.session, guest_user, name="g1")

        self.client.login(username="playersadmin", password="pw")
        response = self.client.post(self.url(), {"delete_all_players_form": "1"})
        self.assertEqual(response.status_code, 200)
        self.assertTrue(response.context["all_players_deleted"])
        self.assertEqual(
            Player.objects.filter(session=self.session, user__is_guest_player=False).count(), 0
        )
        self.assertTrue(Player.objects.filter(session=self.session, name="g1").exists())

    def test_delete_all_random_players_leaves_others_untouched(self):
        create_random_players(self.session, 2)
        u1 = make_user("Player_playersadminsession_regular", is_player=True)
        make_player(self.session, u1, name="regular")

        self.client.login(username="playersadmin", password="pw")
        response = self.client.post(
            self.url(), {"delete_all_random_players_form": "1"}
        )
        self.assertEqual(response.status_code, 200)
        self.assertTrue(response.context["all_random_players_deleted"])
        self.assertEqual(
            Player.objects.filter(session=self.session, user__is_random_player=True).count(), 0
        )
        self.assertTrue(Player.objects.filter(session=self.session, name="regular").exists())

    def test_delete_all_guests_leaves_others_untouched(self):
        guest_user = make_user("Guest_playersadminsession_g2", is_player=True)
        guest_user.is_guest_player = True
        guest_user.save()
        make_player(self.session, guest_user, name="g2")
        u1 = make_user("Player_playersadminsession_regular2", is_player=True)
        make_player(self.session, u1, name="regular2")

        self.client.login(username="playersadmin", password="pw")
        response = self.client.post(self.url(), {"delete_all_guests_form": "1"})
        self.assertEqual(response.status_code, 200)
        self.assertTrue(response.context["all_guests_deleted"])
        self.assertEqual(
            Player.objects.filter(session=self.session, user__is_guest_player=True).count(), 0
        )
        self.assertTrue(Player.objects.filter(session=self.session, name="regular2").exists())

    def test_regular_admin_does_not_see_admin_management_forms(self):
        self.client.login(username="playersadmin", password="pw")
        response = self.client.get(self.url())
        self.assertNotIn("make_admin_form", response.context)

    def test_regular_admin_cannot_promote_via_post(self):
        target = make_user("promotetarget")
        self.client.login(username="playersadmin", password="pw")
        response = self.client.post(
            self.url(),
            {"make_admin_form": "1", "username": "promotetarget", "super_admin": ""},
        )
        self.assertEqual(response.status_code, 200)
        self.assertNotIn(target, self.session.admins.all())

    def test_super_admin_can_promote_user_to_admin_by_username(self):
        self.session.super_admins.add(self.admin)
        target = make_user("promotebyusername")
        self.client.login(username="playersadmin", password="pw")
        response = self.client.post(
            self.url(),
            {"make_admin_form": "1", "username": "promotebyusername", "super_admin": ""},
        )
        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.context["new_admin"], target)
        self.assertIn(target, self.session.admins.all())
        self.assertNotIn(target, self.session.super_admins.all())

    def test_super_admin_can_promote_user_to_super_admin(self):
        self.session.super_admins.add(self.admin)
        target = make_user("promotetosuper")
        self.client.login(username="playersadmin", password="pw")
        response = self.client.post(
            self.url(),
            {"make_admin_form": "1", "username": "promotetosuper", "super_admin": "on"},
        )
        self.assertEqual(response.status_code, 200)
        self.assertIn(target, self.session.super_admins.all())

    def test_super_admin_can_promote_by_player_name(self):
        self.session.super_admins.add(self.admin)
        target_user = make_user("Player_playersadminsession_promo", is_player=True)
        make_player(self.session, target_user, name="promo")
        self.client.login(username="playersadmin", password="pw")
        response = self.client.post(
            self.url(),
            {"make_admin_form": "1", "playername": "promo", "super_admin": ""},
        )
        self.assertEqual(response.status_code, 200)
        self.assertIn(target_user, self.session.admins.all())

    def test_promote_unknown_username_shows_error(self):
        self.session.super_admins.add(self.admin)
        self.client.login(username="playersadmin", password="pw")
        response = self.client.post(
            self.url(),
            {"make_admin_form": "1", "username": "doesnotexist", "super_admin": ""},
        )
        self.assertEqual(response.status_code, 200)
        self.assertTrue(response.context["make_admin_form"].errors)

    def test_super_admin_can_remove_admin(self):
        self.session.super_admins.add(self.admin)
        target = make_user("toberemoved")
        self.session.admins.add(target)
        self.session.super_admins.add(target)
        self.client.login(username="playersadmin", password="pw")
        response = self.client.post(
            self.url(),
            {"remove_admin_form": "1", "remove_admin_id": str(target.id)},
        )
        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.context["removed_admin"], target)
        self.assertNotIn(target, self.session.admins.all())
        self.assertNotIn(target, self.session.super_admins.all())

    def test_super_admins_and_admins_lists_are_split_in_context(self):
        self.session.super_admins.add(self.admin)
        admin_only = make_user("adminonly")
        self.session.admins.add(admin_only)
        self.client.login(username="playersadmin", password="pw")
        response = self.client.get(self.url())
        self.assertIn(self.admin, response.context["super_admins"])
        self.assertIn(admin_only, response.context["admins"])
        self.assertNotIn(self.admin, response.context["admins"])

    def test_admin_gets_players_csv_export(self):
        self.client.login(username="playersadmin", password="pw")
        response = self.client.get(
            reverse("core:session_admin_players_export", args=(self.session.url_tag,))
        )
        self.assertEqual(response.status_code, 200)
        self.assertEqual(response["Content-Type"], "text/csv")


class SessionAdminPlayerPasswordViewTests(TestCase):
    def setUp(self):
        self.session = make_session("pwadminsession", visible=True)
        self.admin = make_user("pwadmin")
        self.session.admins.add(self.admin)
        self.player_user = make_user(
            "Player_pwadminsession_target", is_player=True
        )
        self.player = make_player(self.session, self.player_user, name="target")

    def url(self):
        return reverse(
            "core:session_admin_player_password",
            args=(self.session.url_tag, self.player_user.id),
        )

    def test_non_admin_is_blocked(self):
        make_user("pwintruder")
        self.client.login(username="pwintruder", password="pw")
        response = self.client.get(self.url())
        self.assertEqual(response.status_code, 404)

    def test_404_for_non_player_restricted_user(self):
        global_user = make_user("globaluser", is_player=False)
        self.client.login(username="pwadmin", password="pw")
        response = self.client.get(
            reverse(
                "core:session_admin_player_password",
                args=(self.session.url_tag, global_user.id),
            )
        )
        self.assertEqual(response.status_code, 404)

    def test_admin_can_view_the_form(self):
        self.client.login(username="pwadmin", password="pw")
        response = self.client.get(self.url())
        self.assertEqual(response.status_code, 200)
        self.assertIn("update_password_form", response.context)

    def test_admin_can_reset_player_password(self):
        self.client.login(username="pwadmin", password="pw")
        response = self.client.post(
            self.url(),
            {
                "update_password_form": "1",
                "password1": "NewStrongPass1",
                "password2": "NewStrongPass1",
                "accept_terms": "on",
            },
        )
        self.assertEqual(response.status_code, 200)
        self.player_user.refresh_from_db()
        self.assertTrue(self.player_user.check_password("NewStrongPass1"))

    def test_mismatched_passwords_show_error_and_do_not_change_password(self):
        self.client.login(username="pwadmin", password="pw")
        response = self.client.post(
            self.url(),
            {
                "update_password_form": "1",
                "password1": "NewStrongPass1",
                "password2": "DifferentPass2",
                "accept_terms": "on",
            },
        )
        self.assertEqual(response.status_code, 200)
        self.assertTrue(response.context["update_password_form"].errors)
        self.player_user.refresh_from_db()
        self.assertTrue(self.player_user.check_password("pw"))
