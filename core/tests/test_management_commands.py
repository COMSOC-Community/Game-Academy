import io
import os
import tempfile
from unittest import mock

from django.core.management import call_command
from django.test import TestCase

from core.constants import TEAM_USER_USERNAME, team_player_name
from core.models import CustomUser, Player, Game
from core.tests.helpers import make_session, make_game, make_user, make_player


class InitialiseDbTests(TestCase):
    def test_creates_the_team_user(self):
        call_command("initialise_db")
        team_user = CustomUser.objects.get(username=TEAM_USER_USERNAME)
        self.assertTrue(team_user.is_player)
        self.assertTrue(team_user.is_guest_player)
        self.assertFalse(team_user.is_active)

    def test_is_idempotent_and_does_not_overwrite_an_existing_team_user(self):
        existing = CustomUser.objects.create_user(
            username=TEAM_USER_USERNAME, password="pw",
        )
        existing.is_active = True
        existing.save()

        call_command("initialise_db")

        self.assertEqual(CustomUser.objects.filter(username=TEAM_USER_USERNAME).count(), 1)
        existing.refresh_from_db()
        self.assertTrue(existing.is_active)


class ValidateGameIllustrationsTests(TestCase):
    def setUp(self):
        self.session = make_session("illustrationvalidationsession")

    def run_command(self, *args):
        stderr = io.StringIO()
        call_command("validate_game_illustrations", *args, stderr=stderr, stdout=io.StringIO())
        return stderr.getvalue()

    def test_valid_path_produces_no_error(self):
        make_game(
            self.session, url_tag="numb",
            illustration_path="numbersgame/img/NumbersGame1.png",
        )
        stderr = self.run_command()
        self.assertEqual(stderr, "")

    def test_none_path_is_skipped(self):
        make_game(self.session, url_tag="numb", illustration_path=None)
        stderr = self.run_command()
        self.assertEqual(stderr, "")

    def test_invalid_path_without_autofix_is_reported_but_unchanged(self):
        game = make_game(self.session, url_tag="numb", illustration_path="bogus/path.png")
        stderr = self.run_command()
        self.assertIn("has not been found", stderr)
        game.refresh_from_db()
        self.assertEqual(game.illustration_path, "bogus/path.png")

    def test_invalid_path_with_autofix_is_replaced_by_a_valid_one(self):
        game = make_game(self.session, url_tag="numb", illustration_path="bogus/path.png")
        self.run_command("--auto-fix")
        game.refresh_from_db()
        self.assertIn(game.illustration_path, game.game_config().illustration_paths)

    def test_autofix_prefers_the_illustration_with_the_matching_number(self):
        game = make_game(self.session, url_tag="numb", illustration_path="oldpath3.png")
        self.run_command("--auto-fix")
        game.refresh_from_db()
        self.assertEqual(game.illustration_path, "numbersgame/img/NumbersGame3.png")

    @mock.patch("core.management.commands.validate_game_illustrations.finders.find")
    def test_autofix_reports_when_no_replacement_can_be_found(self, mock_find):
        # Simulate a static folder where none of the game's configured illustrations
        # (nor the broken one) actually resolve to a file.
        mock_find.return_value = None
        game = make_game(self.session, url_tag="numb", illustration_path="bogus/path.png")
        stderr = self.run_command("--auto-fix")
        self.assertIn("None of the path in the game app", stderr)
        game.refresh_from_db()
        self.assertEqual(game.illustration_path, "bogus/path.png")


class ValidateGameViewsTests(TestCase):
    def setUp(self):
        self.session = make_session("viewvalidationsession")

    def run_command(self, *args):
        stderr = io.StringIO()
        call_command("validate_game_views", *args, stderr=stderr, stdout=io.StringIO())
        return stderr.getvalue()

    def test_valid_views_produce_no_error(self):
        make_game(
            self.session, url_tag="numb", initial_view="index", view_after_submit="submit_answer",
        )
        stderr = self.run_command()
        self.assertEqual(stderr, "")

    def test_invalid_initial_view_is_reported_without_autofix(self):
        game = make_game(self.session, url_tag="numb", initial_view="bogus_view")
        stderr = self.run_command()
        self.assertIn("initial view is not valid", stderr)
        game.refresh_from_db()
        self.assertEqual(game.initial_view, "bogus_view")

    def test_invalid_views_are_autofixed_to_the_home_view(self):
        game = make_game(
            self.session, url_tag="numb", initial_view="bogus", view_after_submit="bogus2",
        )
        self.run_command("--auto-fix")
        game.refresh_from_db()
        self.assertEqual(game.initial_view, "index")
        self.assertEqual(game.view_after_submit, "index")

    def test_session_url_tag_filter_limits_scope(self):
        other_session = make_session("otherviewvalidationsession")
        game_in_scope = make_game(
            self.session, url_tag="numb", initial_view="bogus",
        )
        game_out_of_scope = make_game(
            other_session, url_tag="numb", initial_view="bogus",
        )
        self.run_command("--session_url_tag", self.session.url_tag, "--auto-fix")
        game_in_scope.refresh_from_db()
        game_out_of_scope.refresh_from_db()
        self.assertEqual(game_in_scope.initial_view, "index")
        self.assertEqual(game_out_of_scope.initial_view, "bogus")

    def test_autofix_uses_the_configured_home_view_when_set(self):
        game = make_game(self.session, url_tag="numb", initial_view="bogus")
        with mock.patch.object(game.game_config(), "home_view", "submit_answer"):
            self.run_command("--auto-fix")
        game.refresh_from_db()
        self.assertEqual(game.initial_view, "submit_answer")

    def test_autofix_falls_back_to_first_available_view_when_no_index(self):
        game = make_game(self.session, url_tag="numb", initial_view="bogus")
        with mock.patch.object(
            Game, "all_url_names", return_value=("submit_answer", "global_results")
        ):
            self.run_command("--auto-fix")
        game.refresh_from_db()
        self.assertEqual(game.initial_view, "submit_answer")


class GenerateRandomPlayersCommandTests(TestCase):
    def setUp(self):
        self.session = make_session("genrandomplayerssession")

    def run_command(self, *args, **kwargs):
        stderr = io.StringIO()
        stdout = io.StringIO()
        call_command(
            "generate_random_players", *args, stderr=stderr, stdout=stdout, **kwargs
        )
        return stdout.getvalue(), stderr.getvalue()

    def test_missing_session_argument_reports_error(self):
        _, stderr = self.run_command(3, session="")
        self.assertIn("session", stderr)

    def test_unknown_session_reports_error(self):
        _, stderr = self.run_command(3, session="doesnotexist")
        self.assertIn("no session", stderr)

    def test_zero_players_reports_error(self):
        _, stderr = self.run_command(0, session=self.session.url_tag)
        self.assertIn("at least 1", stderr)

    def test_negative_players_reports_error(self):
        _, stderr = self.run_command(-1, session=self.session.url_tag)
        self.assertIn("at least 1", stderr)

    def test_creates_the_requested_number_of_players(self):
        stdout, stderr = self.run_command(4, session=self.session.url_tag)
        self.assertEqual(stderr, "")
        self.assertIn("4 players populated", stdout)
        self.assertEqual(Player.objects.filter(session=self.session).count(), 4)


class GenerateRandomAnswersCommandTests(TestCase):
    def setUp(self):
        self.session = make_session("genrandomanswerssession")
        self.game = make_game(self.session, url_tag="numb")
        from numbersgame.models import Setting

        Setting.objects.create(game=self.game, lower_bound=0, upper_bound=100)

    def run_command(self, *args, **kwargs):
        stderr = io.StringIO()
        stdout = io.StringIO()
        call_command(
            "generate_random_answers", *args, stderr=stderr, stdout=stdout, **kwargs
        )
        return stdout.getvalue(), stderr.getvalue()

    def test_missing_session_argument_reports_error(self):
        _, stderr = self.run_command(3, session="", game=self.game.url_tag)
        self.assertIn("session", stderr)

    def test_unknown_session_reports_error(self):
        _, stderr = self.run_command(3, session="doesnotexist", game=self.game.url_tag)
        self.assertIn("no session", stderr)

    def test_missing_game_argument_reports_error(self):
        _, stderr = self.run_command(3, session=self.session.url_tag, game="")
        self.assertIn("game", stderr)

    def test_unknown_game_reports_error(self):
        _, stderr = self.run_command(3, session=self.session.url_tag, game="doesnotexist")
        self.assertIn("no game", stderr)

    def test_zero_answers_reports_error(self):
        _, stderr = self.run_command(0, session=self.session.url_tag, game=self.game.url_tag)
        self.assertIn("at least 1", stderr)

    def test_game_without_random_answers_func_reports_error(self):
        other_game = make_game(
            self.session, url_tag="othr", game_type="goodbadgame", name="Other",
        )
        with mock.patch.object(other_game.game_config(), "random_answers_func", None):
            _, stderr = self.run_command(
                3, session=self.session.url_tag, game=other_game.url_tag
            )
        self.assertIn("not configured to generate random answers", stderr)

    def test_creates_the_requested_number_of_answers(self):
        from numbersgame.models import Answer

        stdout, stderr = self.run_command(
            3, session=self.session.url_tag, game=self.game.url_tag
        )
        self.assertEqual(stderr, "")
        self.assertIn("3 random answers", stdout)
        self.assertEqual(Answer.objects.filter(game=self.game).count(), 3)

    def test_needs_teams_branch_creates_teams_instead_of_players(self):
        from numbersgame.models import Answer

        CustomUser.objects.create_user(username=TEAM_USER_USERNAME, password="pw")
        team_game = make_game(
            self.session, url_tag="team", name="TeamGame", needs_teams=True,
        )
        from numbersgame.models import Setting

        Setting.objects.create(game=team_game, lower_bound=0, upper_bound=100)
        stdout, stderr = self.run_command(
            2, session=self.session.url_tag, game=team_game.url_tag
        )
        self.assertEqual(stderr, "")
        self.assertEqual(Answer.objects.filter(game=team_game).count(), 2)
        answering_players = {
            a.player for a in Answer.objects.filter(game=team_game)
        }
        self.assertTrue(all(p.is_team_player for p in answering_players))

    @mock.patch("core.management.commands.generate_random_answers.management.call_command")
    def test_run_management_flag_triggers_configured_commands(self, mock_call_command):
        self.run_command(
            2, session=self.session.url_tag, game=self.game.url_tag, run_management=True,
        )
        mock_call_command.assert_called_once_with(
            "numbersgame_results",
            session=self.session.url_tag,
            game=self.game.url_tag,
            stdout=mock.ANY,
        )

    @mock.patch("core.management.commands.generate_random_answers.management.call_command")
    def test_run_management_flag_off_skips_configured_commands(self, mock_call_command):
        self.run_command(2, session=self.session.url_tag, game=self.game.url_tag)
        mock_call_command.assert_not_called()


class ImportPlayersCsvCommandTests(TestCase):
    def setUp(self):
        self.session = make_session("importcsvcmdsession")

    def write_csv(self, content):
        fd, path = tempfile.mkstemp(suffix=".csv")
        with os.fdopen(fd, "w", encoding="utf-8", newline="") as f:
            f.write(content)
        self.addCleanup(os.remove, path)
        return path

    def run_command(self, csv_path, session_url_tag):
        stdout = io.StringIO()
        call_command("import_players_csv", csv_path, session_url_tag, stdout=stdout)
        return stdout.getvalue()

    def test_unknown_session_reports_error(self):
        path = self.write_csv("username\nalice\n")
        stdout = self.run_command(path, "doesnotexist")
        self.assertIn("does not exist", stdout)
        self.assertEqual(Player.objects.count(), 0)

    def test_missing_username_column_raises(self):
        path = self.write_csv("notusername\nalice\n")
        with self.assertRaises(ValueError):
            self.run_command(path, self.session.url_tag)

    def test_invalid_slug_username_is_skipped(self):
        path = self.write_csv("username\nnot a valid slug!\n")
        stdout = self.run_command(path, self.session.url_tag)
        self.assertIn("not a valid slug", stdout)
        self.assertIn("0 players imported, 1 failures", stdout)
        self.assertEqual(Player.objects.filter(session=self.session).count(), 0)

    def test_duplicate_username_is_skipped(self):
        user = make_user("importcsvexisting")
        make_player(self.session, user, name="importcsvexisting")
        path = self.write_csv("username\nimportcsvexisting\n")
        stdout = self.run_command(path, self.session.url_tag)
        self.assertIn("already used", stdout)
        self.assertIn("0 players imported, 1 failures", stdout)

    def test_valid_row_creates_player_with_default_password(self):
        path = self.write_csv("username\nimportcsvnew\n")
        stdout = self.run_command(path, self.session.url_tag)
        self.assertIn("No password was provided", stdout)
        self.assertIn("1 players imported, 0 failures", stdout)
        player = Player.objects.get(session=self.session, name="importcsvnew")
        self.assertTrue(player.user.check_password("thisisthegameserver"))

    def test_password_with_whitespace_is_stripped(self):
        path = self.write_csv("username,password\nimportcsvpw, secretpw \n")
        stdout = self.run_command(path, self.session.url_tag)
        self.assertIn("leading and/or trailing whitespaces", stdout)
        player = Player.objects.get(session=self.session, name="importcsvpw")
        self.assertTrue(player.user.check_password("secretpw"))

    def test_email_is_stripped_and_stored(self):
        path = self.write_csv("username,email\nimportcsvemail, someone@example.com \n")
        self.run_command(path, self.session.url_tag)
        player = Player.objects.get(session=self.session, name="importcsvemail")
        self.assertEqual(player.user.email, "someone@example.com")

    def test_multiple_rows_mixed_success_and_failure(self):
        path = self.write_csv(
            "username\nimportcsvgood\nnot a valid slug!\n"
        )
        stdout = self.run_command(path, self.session.url_tag)
        self.assertIn("1 players imported, 1 failures", stdout)
