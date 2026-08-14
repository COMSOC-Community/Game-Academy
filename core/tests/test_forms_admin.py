from django.core.files.uploadedfile import SimpleUploadedFile
from django.test import TestCase, override_settings

from core.forms import (
    CreateSessionForm,
    DeleteSessionForm,
    CreateGameForm,
    ImportCSVFileForm,
    validate_csv_file,
    RandomPlayersForm,
    RandomAnswersForm,
    MakeAdminForm,
    CreateTeamForm,
    JoinPrivateTeamForm,
    JoinPublicTeamForm,
)
from core.models import Team, Player, CustomUser
from core.constants import TEAM_USER_USERNAME
from core.tests.helpers import make_session, make_user, make_game, make_player
from django import forms as django_forms


def valid_create_session_data(**overrides):
    data = {
        "url_tag": "brandnewsession",
        "name": "Brand New Session",
        "long_name": "The Brand New Session",
        "show_guest_login": "on",
        "show_user_login": "on",
        "show_create_account": "on",
        "visible": "on",
    }
    data.update(overrides)
    return data


class CreateSessionFormTests(TestCase):
    @override_settings(DEBUG=True)
    def test_valid_data_is_accepted_on_creation(self):
        form = CreateSessionForm(valid_create_session_data())
        self.assertTrue(form.is_valid())

    @override_settings(DEBUG=True)
    def test_duplicate_url_tag_is_rejected(self):
        make_session("brandnewsession")
        form = CreateSessionForm(valid_create_session_data())
        self.assertFalse(form.is_valid())
        self.assertIn("url_tag", form.errors)

    @override_settings(DEBUG=True)
    def test_forbidden_url_tag_is_rejected(self):
        form = CreateSessionForm(valid_create_session_data(url_tag="admin"))
        self.assertFalse(form.is_valid())
        self.assertIn("url_tag", form.errors)

    @override_settings(DEBUG=True)
    def test_duplicate_name_is_rejected(self):
        make_session("someothersession", name="Brand New Session")
        form = CreateSessionForm(valid_create_session_data())
        self.assertFalse(form.is_valid())
        self.assertIn("name", form.errors)

    @override_settings(DEBUG=True)
    def test_duplicate_long_name_is_rejected(self):
        make_session("someothersession2", long_name="The Brand New Session")
        form = CreateSessionForm(valid_create_session_data())
        self.assertFalse(form.is_valid())
        self.assertIn("long_name", form.errors)

    def test_creation_mode_pops_advanced_fields(self):
        form = CreateSessionForm()
        for field in ("game_after_logging", "show_side_panel", "show_game_nav_home", "show_game_nav_result"):
            self.assertNotIn(field, form.fields)
        self.assertIn("captcha", form.fields)

    def test_edit_mode_disables_url_tag_and_drops_captcha(self):
        session = make_session("editablesession")
        form = CreateSessionForm(session=session)
        self.assertTrue(form.fields["url_tag"].disabled)
        self.assertNotIn("captcha", form.fields)

    def test_edit_mode_keeping_same_name_is_valid(self):
        session = make_session("editablesession2", name="Keep This Name")
        form = CreateSessionForm(
            {
                "url_tag": session.url_tag,
                "name": "Keep This Name",
                "long_name": session.long_name,
                "show_side_panel": "on",
                "show_game_nav_home": "on",
                "show_game_nav_result": "on",
            },
            session=session,
        )
        self.assertTrue(form.is_valid())

    def test_edit_mode_pops_game_after_logging_when_no_games(self):
        session = make_session("editablesession3")
        form = CreateSessionForm(session=session)
        self.assertNotIn("game_after_logging", form.fields)

    def test_edit_mode_offers_game_after_logging_when_games_exist(self):
        session = make_session("editablesession4")
        game = make_game(session, url_tag="numb")
        form = CreateSessionForm(session=session)
        self.assertIn("game_after_logging", form.fields)
        self.assertIn(game, form.fields["game_after_logging"].queryset)


class DeleteSessionFormTests(TestCase):
    def setUp(self):
        self.user = make_user("deletesessionformuser")

    def test_correct_password_is_accepted(self):
        form = DeleteSessionForm({"delete": "on", "password": "pw"}, user=self.user)
        self.assertTrue(form.is_valid())

    def test_wrong_password_is_rejected(self):
        form = DeleteSessionForm({"delete": "on", "password": "wrongpw"}, user=self.user)
        self.assertFalse(form.is_valid())


def valid_create_game_data(**overrides):
    data = {
        "game_type": "numbersgame",
        "name": "A New Game",
        "url_tag": "newg",
        "visible": "on",
        "playable": "on",
        "results_visible": "on",
        "needs_teams": "",
        "description": "",
    }
    data.update(overrides)
    return data


class CreateGameFormTests(TestCase):
    def setUp(self):
        self.session = make_session("creategameformsession")

    def test_valid_data_is_accepted(self):
        form = CreateGameForm(valid_create_game_data(), session=self.session)
        self.assertTrue(form.is_valid())

    def test_duplicate_name_is_rejected(self):
        make_game(self.session, url_tag="othr", name="A New Game")
        form = CreateGameForm(valid_create_game_data(), session=self.session)
        self.assertFalse(form.is_valid())
        self.assertIn("name", form.errors)

    def test_duplicate_url_tag_is_rejected(self):
        make_game(self.session, url_tag="newg", name="Some Other Name")
        form = CreateGameForm(valid_create_game_data(), session=self.session)
        self.assertFalse(form.is_valid())
        self.assertIn("url_tag", form.errors)

    def test_creation_mode_pops_advanced_fields(self):
        form = CreateGameForm(session=self.session)
        for field in (
            "illustration_path", "ordering_priority", "run_management_after_submit",
            "initial_view", "view_after_submit",
        ):
            self.assertNotIn(field, form.fields)

    def test_edit_mode_disables_game_type_and_populates_choices(self):
        game = make_game(self.session, url_tag="numb")
        form = CreateGameForm(session=self.session, game=game)
        self.assertTrue(form.fields["game_type"].disabled)
        self.assertIn("index", [c[0] for c in form.fields["initial_view"].choices])
        self.assertIn("illustration_path", form.fields)

    def test_edit_mode_keeping_same_name_is_valid(self):
        game = make_game(self.session, url_tag="numb", name="Keep This Game Name")
        form = CreateGameForm(
            {
                "game_type": "numbersgame",
                "name": "Keep This Game Name",
                "url_tag": "numb",
                "visible": "on",
                "playable": "on",
                "results_visible": "on",
                "needs_teams": "",
                "description": "",
                "illustration_path": "numbersgame/img/NumbersGame1.png",
                "ordering_priority": "0",
                "run_management_after_submit": "",
                "initial_view": "index",
                "view_after_submit": "index",
            },
            session=self.session, game=game,
        )
        self.assertTrue(form.is_valid())


class ValidateCsvFileTests(TestCase):
    def test_valid_csv_passes(self):
        f = SimpleUploadedFile("players.csv", b"username\nalice\nbob\n", content_type="text/csv")
        # Should not raise.
        validate_csv_file(f)

    def test_wrong_extension_is_rejected(self):
        f = SimpleUploadedFile("players.txt", b"username\nalice\n", content_type="text/plain")
        with self.assertRaises(django_forms.ValidationError):
            validate_csv_file(f)

    def test_missing_header_is_rejected(self):
        f = SimpleUploadedFile("players.csv", b"", content_type="text/csv")
        with self.assertRaises(django_forms.ValidationError):
            validate_csv_file(f)

    def test_uneven_row_length_is_rejected(self):
        f = SimpleUploadedFile(
            "players.csv", b"username,password\nalice,secret,extra\n", content_type="text/csv"
        )
        with self.assertRaises(django_forms.ValidationError):
            validate_csv_file(f)


class ImportCSVFileFormTests(TestCase):
    def test_valid_file_is_accepted(self):
        f = SimpleUploadedFile("players.csv", b"username\nalice\n", content_type="text/csv")
        form = ImportCSVFileForm(files={"csv_file": f})
        self.assertTrue(form.is_valid())

    def test_wrong_extension_is_rejected(self):
        f = SimpleUploadedFile("players.txt", b"username\nalice\n", content_type="text/plain")
        form = ImportCSVFileForm(files={"csv_file": f})
        self.assertFalse(form.is_valid())


class RandomPlayersFormTests(TestCase):
    def test_minimum_boundary(self):
        self.assertTrue(RandomPlayersForm({"num_players": "1"}).is_valid())

    def test_zero_is_rejected(self):
        self.assertFalse(RandomPlayersForm({"num_players": "0"}).is_valid())

    def test_maximum_boundary(self):
        self.assertTrue(RandomPlayersForm({"num_players": "50"}).is_valid())

    def test_above_maximum_is_rejected(self):
        self.assertFalse(RandomPlayersForm({"num_players": "51"}).is_valid())


class RandomAnswersFormTests(TestCase):
    def test_minimum_boundary(self):
        form = RandomAnswersForm({"num_answers": "1", "run_management": ""})
        self.assertTrue(form.is_valid())

    def test_zero_is_rejected(self):
        form = RandomAnswersForm({"num_answers": "0", "run_management": ""})
        self.assertFalse(form.is_valid())

    def test_above_maximum_is_rejected(self):
        form = RandomAnswersForm({"num_answers": "51", "run_management": ""})
        self.assertFalse(form.is_valid())


class MakeAdminFormTests(TestCase):
    def setUp(self):
        self.session = make_session("makeadminformsession")

    def test_neither_username_nor_playername_is_rejected(self):
        form = MakeAdminForm({"username": "", "playername": "", "super_admin": ""}, session=self.session)
        self.assertFalse(form.is_valid())

    def test_both_username_and_playername_is_rejected(self):
        make_user("bothfielduser")
        form = MakeAdminForm(
            {"username": "bothfielduser", "playername": "someone", "super_admin": ""},
            session=self.session,
        )
        self.assertFalse(form.is_valid())

    def test_valid_by_username(self):
        target = make_user("makeadminbyusername")
        form = MakeAdminForm(
            {"username": "makeadminbyusername", "playername": "", "super_admin": ""},
            session=self.session,
        )
        self.assertTrue(form.is_valid())
        self.assertEqual(form.cleaned_data["user"], target)

    def test_unknown_username_is_rejected(self):
        form = MakeAdminForm(
            {"username": "nosuchuser", "playername": "", "super_admin": ""}, session=self.session
        )
        self.assertFalse(form.is_valid())
        self.assertIn("username", form.errors)

    def test_valid_by_playername(self):
        target_user = make_user("Player_makeadminformsession_p1")
        make_player(self.session, target_user, name="p1")
        form = MakeAdminForm(
            {"username": "", "playername": "p1", "super_admin": "on"}, session=self.session
        )
        self.assertTrue(form.is_valid())
        self.assertEqual(form.cleaned_data["user"], target_user)

    def test_unknown_playername_is_rejected(self):
        form = MakeAdminForm(
            {"username": "", "playername": "nosuchplayer", "super_admin": ""}, session=self.session
        )
        self.assertFalse(form.is_valid())
        self.assertIn("playername", form.errors)


class TeamFormsTestsBase(TestCase):
    def setUp(self):
        CustomUser.objects.create_user(username=TEAM_USER_USERNAME, password="pw")
        self.session = make_session("teamformssession")
        self.game = make_game(self.session, url_tag="numb", needs_teams=True)
        self.creator_user = make_user("teamformscreator")
        self.creator_player = make_player(self.session, self.creator_user, name="teamformscreator")

    def make_team(self, name, is_public=True):
        team_user = CustomUser.objects.get(username=TEAM_USER_USERNAME)
        team_player = Player.objects.create(
            user=team_user, name=f"TeamPlayer_{name}", session=self.session, is_team_player=True,
        )
        return Team.objects.create(
            name=name, game=self.game, creator=self.creator_player, is_public=is_public,
            team_player=team_player,
        )


class CreateTeamFormTests(TeamFormsTestsBase):
    def test_valid_name_is_accepted(self):
        form = CreateTeamForm({"name": "Fresh Team", "is_public": "on"}, game=self.game)
        self.assertTrue(form.is_valid())

    def test_duplicate_name_in_same_game_is_rejected(self):
        self.make_team("Taken Team")
        form = CreateTeamForm({"name": "Taken Team", "is_public": "on"}, game=self.game)
        self.assertFalse(form.is_valid())

    def test_same_name_in_a_different_game_is_allowed(self):
        other_game = make_game(self.session, url_tag="othr", name="Other Game", needs_teams=True)
        self.make_team("Shared Name")
        form = CreateTeamForm({"name": "Shared Name", "is_public": "on"}, game=other_game)
        self.assertTrue(form.is_valid())


class JoinPrivateTeamFormTests(TeamFormsTestsBase):
    def test_valid_team_name_sets_team_in_cleaned_data(self):
        team = self.make_team("PrivateOne", is_public=False)
        form = JoinPrivateTeamForm({"name": "PrivateOne"}, game=self.game)
        self.assertTrue(form.is_valid())
        self.assertEqual(form.cleaned_data["team"], team)

    def test_unknown_team_name_is_rejected(self):
        form = JoinPrivateTeamForm({"name": "NoSuchTeam"}, game=self.game)
        self.assertFalse(form.is_valid())


class JoinPublicTeamFormTests(TeamFormsTestsBase):
    def test_queryset_only_contains_public_teams_of_this_game(self):
        public_team = self.make_team("PublicOne", is_public=True)
        self.make_team("PrivateTwo", is_public=False)
        form = JoinPublicTeamForm(game=self.game)
        self.assertEqual(list(form.fields["team"].queryset), [public_team])

    def test_team_count_reflects_number_of_public_teams(self):
        form = JoinPublicTeamForm(game=self.game)
        self.assertEqual(form.team_count, 0)
        self.make_team("PublicA", is_public=True)
        form = JoinPublicTeamForm(game=self.game)
        self.assertEqual(form.team_count, 1)

    def test_team_to_label_includes_creator_display_name(self):
        team = self.make_team("PublicLabelTeam", is_public=True)
        label = JoinPublicTeamForm.team_to_label(team)
        self.assertIn("PublicLabelTeam", label)
        self.assertIn(self.creator_player.display_name(), label)
