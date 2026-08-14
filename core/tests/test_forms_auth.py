from django import forms as django_forms
from django.test import TestCase, override_settings

from core.forms import (
    DebugSafeReCaptchaField,
    SessionFinderForm,
    LoginForm,
    UserRegistrationForm,
    UpdatePasswordForm,
    DeleteAccountForm,
    PlayerLoginForm,
    PlayerRegistrationForm,
    SessionGuestRegistration,
)
from core.tests.helpers import make_session, make_user, make_player


class DebugSafeReCaptchaFieldTests(TestCase):
    @override_settings(DEBUG=True)
    def test_bypasses_validation_when_debug_true(self):
        field = DebugSafeReCaptchaField()
        # Should not raise even though no real captcha token is given.
        field.clean("")

    def test_still_required_when_debug_false(self):
        # The Django test runner forces settings.DEBUG = False, so no override needed here.
        field = DebugSafeReCaptchaField()
        with self.assertRaises(django_forms.ValidationError):
            field.clean("")


class SessionFinderFormTests(TestCase):
    def test_valid_name_resolves_session_url_tag(self):
        session = make_session("finderurltag", name="Finder Session")
        form = SessionFinderForm({"session_name": "Finder Session"})
        self.assertTrue(form.is_valid())
        self.assertEqual(form.cleaned_data["session_url_tag"], session.url_tag)

    def test_unknown_name_is_invalid(self):
        form = SessionFinderForm({"session_name": "No Such Session"})
        self.assertFalse(form.is_valid())


class LoginFormTests(TestCase):
    def test_valid_credentials(self):
        make_user("loginformuser")
        form = LoginForm({"username": "loginformuser", "password": "pw"})
        self.assertTrue(form.is_valid())

    def test_wrong_password_is_invalid(self):
        make_user("loginformuser2")
        form = LoginForm({"username": "loginformuser2", "password": "wrong"})
        self.assertFalse(form.is_valid())

    def test_unknown_username_is_invalid(self):
        form = LoginForm({"username": "nosuchuser", "password": "pw"})
        self.assertFalse(form.is_valid())


def valid_registration_data(**overrides):
    data = {
        "username": "newregistrant",
        "email": "newregistrant@example.com",
        "password1": "StrongPass123",
        "password2": "StrongPass123",
        "accept_terms": "on",
    }
    data.update(overrides)
    return data


class UserRegistrationFormTests(TestCase):
    @override_settings(DEBUG=True)
    def test_valid_data_is_accepted(self):
        form = UserRegistrationForm(valid_registration_data())
        self.assertTrue(form.is_valid())

    @override_settings(DEBUG=True)
    def test_forbidden_username_is_rejected(self):
        form = UserRegistrationForm(valid_registration_data(username="TeamUser"))
        self.assertFalse(form.is_valid())
        self.assertIn("username", form.errors)

    @override_settings(DEBUG=True)
    def test_duplicate_username_is_rejected(self):
        make_user("takenusername")
        form = UserRegistrationForm(valid_registration_data(username="takenusername"))
        self.assertFalse(form.is_valid())
        self.assertIn("username", form.errors)

    @override_settings(DEBUG=True)
    def test_duplicate_email_is_rejected(self):
        existing = make_user("someoneelse")
        existing.email = "taken@example.com"
        existing.save()
        form = UserRegistrationForm(valid_registration_data(email="taken@example.com"))
        self.assertFalse(form.is_valid())
        self.assertIn("email", form.errors)

    @override_settings(DEBUG=True)
    def test_short_password_is_rejected(self):
        form = UserRegistrationForm(
            valid_registration_data(password1="short1", password2="short1")
        )
        self.assertFalse(form.is_valid())
        self.assertIn("password1", form.errors)

    @override_settings(DEBUG=True)
    def test_mismatched_passwords_are_rejected(self):
        form = UserRegistrationForm(
            valid_registration_data(password2="SomethingDifferent1")
        )
        self.assertFalse(form.is_valid())
        self.assertIn("password2", form.errors)

    def test_edit_mode_for_regular_user_disables_username_and_drops_captcha_and_email(self):
        user = make_user("editableuser")
        form = UserRegistrationForm(user=user)
        self.assertNotIn("email", form.fields)
        self.assertNotIn("captcha", form.fields)
        self.assertTrue(form.fields["username"].disabled)
        self.assertEqual(form.fields["username"].initial, "editableuser")

    def test_edit_mode_for_player_restricted_user_uses_player_name_as_initial(self):
        session = make_session("editformsession")
        user = make_user("Player_editformsession_ed", is_player=True)
        make_player(session, user, name="ed")
        form = UserRegistrationForm(user=user)
        self.assertEqual(form.fields["username"].initial, "ed")


class UpdatePasswordFormTests(TestCase):
    def setUp(self):
        self.user = make_user("updatepwuser")

    def test_valid_change_is_accepted(self):
        form = UpdatePasswordForm(
            {"old_password": "pw", "new_password1": "NewStrongPass1", "new_password2": "NewStrongPass1"},
            user=self.user,
        )
        self.assertTrue(form.is_valid())

    def test_wrong_old_password_is_rejected(self):
        form = UpdatePasswordForm(
            {"old_password": "wrongpw", "new_password1": "NewStrongPass1", "new_password2": "NewStrongPass1"},
            user=self.user,
        )
        self.assertFalse(form.is_valid())
        self.assertIn("old_password", form.errors)

    def test_short_new_password_is_rejected(self):
        form = UpdatePasswordForm(
            {"old_password": "pw", "new_password1": "short1", "new_password2": "short1"},
            user=self.user,
        )
        self.assertFalse(form.is_valid())
        self.assertIn("new_password1", form.errors)

    def test_mismatched_new_passwords_are_rejected(self):
        form = UpdatePasswordForm(
            {"old_password": "pw", "new_password1": "NewStrongPass1", "new_password2": "Different2"},
            user=self.user,
        )
        self.assertFalse(form.is_valid())
        self.assertIn("new_password2", form.errors)


class DeleteAccountFormTests(TestCase):
    def setUp(self):
        self.user = make_user("deleteformuser")

    def test_correct_password_is_accepted(self):
        form = DeleteAccountForm({"delete": "on", "password": "pw"}, user=self.user)
        self.assertTrue(form.is_valid())

    def test_wrong_password_is_rejected(self):
        form = DeleteAccountForm({"delete": "on", "password": "wrongpw"}, user=self.user)
        self.assertFalse(form.is_valid())
        self.assertIn("password", form.errors)


class PlayerLoginFormTests(TestCase):
    def setUp(self):
        self.session = make_session("playerloginformsession")
        self.user = make_user("Player_playerloginformsession_pat")
        self.player = make_player(self.session, self.user, name="pat")

    def test_valid_login_by_player_name(self):
        form = PlayerLoginForm(
            {"player_name": "pat", "password": "pw", "search_user": ""}, session=self.session
        )
        self.assertTrue(form.is_valid())
        self.assertEqual(form.cleaned_data["player"], self.player)
        self.assertEqual(form.cleaned_data["user"], self.user)

    def test_player_name_is_case_insensitive(self):
        form = PlayerLoginForm(
            {"player_name": "PAT", "password": "pw", "search_user": ""}, session=self.session
        )
        self.assertTrue(form.is_valid())

    def test_unknown_player_name_is_rejected(self):
        form = PlayerLoginForm(
            {"player_name": "nosuchplayer", "password": "pw", "search_user": ""},
            session=self.session,
        )
        self.assertFalse(form.is_valid())
        self.assertIn("player_name", form.errors)

    def test_wrong_password_is_rejected(self):
        form = PlayerLoginForm(
            {"player_name": "pat", "password": "wrongpw", "search_user": ""}, session=self.session
        )
        self.assertFalse(form.is_valid())
        self.assertIn("password", form.errors)

    def test_search_user_mode_finds_by_username(self):
        form = PlayerLoginForm(
            {"player_name": "Player_playerloginformsession_pat", "password": "pw", "search_user": "on"},
            session=self.session,
        )
        self.assertTrue(form.is_valid())
        self.assertEqual(form.cleaned_data["user"], self.user)
        self.assertEqual(form.cleaned_data["player"], self.player)

    def test_search_user_mode_unknown_username_is_rejected(self):
        form = PlayerLoginForm(
            {"player_name": "nosuchusername", "password": "pw", "search_user": "on"},
            session=self.session,
        )
        self.assertFalse(form.is_valid())

    def test_search_user_mode_user_without_player_profile_has_no_player_in_cleaned_data(self):
        make_user("globalnoplayer")
        form = PlayerLoginForm(
            {"player_name": "globalnoplayer", "password": "pw", "search_user": "on"},
            session=self.session,
        )
        self.assertTrue(form.is_valid())
        self.assertIn("user", form.cleaned_data)
        self.assertNotIn("player", form.cleaned_data)


def valid_player_registration_data(**overrides):
    data = {
        "player_name": "newplayerform",
        "password1": "StrongPass123",
        "password2": "StrongPass123",
        "accept_terms": "on",
    }
    data.update(overrides)
    return data


class PlayerRegistrationFormTests(TestCase):
    def setUp(self):
        self.session = make_session("playerregformsession")

    @override_settings(DEBUG=True)
    def test_valid_data_is_accepted(self):
        form = PlayerRegistrationForm(valid_player_registration_data(), session=self.session)
        self.assertTrue(form.is_valid())

    @override_settings(DEBUG=True)
    def test_duplicate_name_is_rejected(self):
        user = make_user("Player_playerregformsession_taken")
        make_player(self.session, user, name="taken")
        form = PlayerRegistrationForm(
            valid_player_registration_data(player_name="taken"), session=self.session
        )
        self.assertFalse(form.is_valid())
        self.assertIn("player_name", form.errors)

    @override_settings(DEBUG=True)
    def test_mismatched_passwords_are_rejected(self):
        form = PlayerRegistrationForm(
            valid_player_registration_data(password2="Different123"), session=self.session
        )
        self.assertFalse(form.is_valid())

    def test_passwords_display_false_drops_password_fields(self):
        form = PlayerRegistrationForm(
            session=self.session, passwords_display=False
        )
        self.assertNotIn("password1", form.fields)
        self.assertNotIn("password2", form.fields)

    def test_player_edit_mode_disables_name_and_drops_captcha(self):
        user = make_user("Player_playerregformsession_ed2")
        player = make_player(self.session, user, name="ed2")
        form = PlayerRegistrationForm(session=self.session, player=player)
        self.assertTrue(form.fields["player_name"].disabled)
        self.assertEqual(form.fields["player_name"].initial, "ed2")
        self.assertNotIn("captcha", form.fields)


class SessionGuestRegistrationTests(TestCase):
    def setUp(self):
        self.session = make_session("guestformsession")

    @override_settings(DEBUG=True)
    def test_valid_data_is_accepted(self):
        form = SessionGuestRegistration(
            {"guest_name": "newguestform", "accept_terms": "on"}, session=self.session
        )
        self.assertTrue(form.is_valid())
        self.assertIn("guest_username", form.cleaned_data)

    @override_settings(DEBUG=True)
    def test_duplicate_name_in_same_session_is_rejected(self):
        user = make_user("Guest_guestformsession_taken")
        make_player(self.session, user, name="takenguest")
        form = SessionGuestRegistration(
            {"guest_name": "takenguest", "accept_terms": "on"}, session=self.session
        )
        self.assertFalse(form.is_valid())

    @override_settings(DEBUG=True)
    def test_duplicate_name_check_is_not_scoped_to_the_session(self):
        # clean_guest_name checks Player.objects.filter(name=guest_name) with no session
        # filter, so a player name used in a *different* session also blocks registration
        # here. This documents that (possibly surprising) current behaviour.
        other_session = make_session("otherguestformsession")
        user = make_user("Guest_otherguestformsession_shared")
        make_player(other_session, user, name="sharedname")
        form = SessionGuestRegistration(
            {"guest_name": "sharedname", "accept_terms": "on"}, session=self.session
        )
        self.assertFalse(form.is_valid())
