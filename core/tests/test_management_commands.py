import io

from django.core.management import call_command
from django.test import TestCase

from core.constants import TEAM_USER_USERNAME
from core.models import CustomUser
from core.tests.helpers import make_session, make_game


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
