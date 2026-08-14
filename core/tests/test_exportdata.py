import csv
import io

from django.test import TestCase

from core.constants import TEAM_USER_USERNAME, TEAM_USER_PASSWORD
from core.exportdata import session_to_csv, team_to_csv, player_to_csv, games_to_csv
from core.models import CustomUser, Player, Team
from core.tests.helpers import make_session, make_user, make_game, make_player


def read_csv(buffer):
    return list(csv.reader(io.StringIO(buffer.getvalue())))


class SessionToCsvTests(TestCase):
    def test_header_row(self):
        session = make_session("exportsession1")
        buffer = io.StringIO()
        session_to_csv(buffer, session)
        rows = read_csv(buffer)
        self.assertEqual(
            rows[0],
            [
                "url_tag", "name", "long_name", "show_create_account", "show_guest_login",
                "show_user_login", "visible", "admins", "super_admins", "game_after_logging",
            ],
        )

    def test_basic_fields_and_no_admins(self):
        session = make_session(
            "exportsession2", name="Export Session", long_name="The Export Session",
            show_create_account=True, show_guest_login=False, show_user_login=True,
            visible=True,
        )
        buffer = io.StringIO()
        session_to_csv(buffer, session)
        rows = read_csv(buffer)
        self.assertEqual(
            rows[1],
            [
                "exportsession2", "Export Session", "The Export Session",
                "True", "False", "True", "True", "", "", "",
            ],
        )

    def test_admins_and_super_admins_are_semicolon_joined(self):
        session = make_session("exportsession3")
        admin = make_user("csvadmin")
        super_admin = make_user("csvsuperadmin")
        session.admins.add(admin, super_admin)
        session.super_admins.add(super_admin)
        buffer = io.StringIO()
        session_to_csv(buffer, session)
        rows = read_csv(buffer)
        self.assertEqual(set(rows[1][7].split(";")), {"csvadmin", "csvsuperadmin"})
        self.assertEqual(rows[1][8], "csvsuperadmin")

    def test_game_after_logging_is_stringified(self):
        session = make_session("exportsession4")
        game = make_game(session, url_tag="numb")
        session.game_after_logging = game
        session.save()
        buffer = io.StringIO()
        session_to_csv(buffer, session)
        rows = read_csv(buffer)
        self.assertEqual(rows[1][9], str(game))


class PlayerToCsvTests(TestCase):
    def test_header_row(self):
        session = make_session("exportplayersession1")
        buffer = io.StringIO()
        player_to_csv(buffer, session)
        rows = read_csv(buffer)
        self.assertEqual(rows[0], ["player_name", "is_guest", "is_team_player"])

    def test_regular_guest_and_team_players_are_flagged_correctly(self):
        session = make_session("exportplayersession2")

        regular_user = make_user("regularplayerexp")
        make_player(session, regular_user, name="regularplayerexp")

        guest_user = make_user("guestplayerexp")
        guest_user.is_guest_player = True
        guest_user.save()
        make_player(session, guest_user, name="guestplayerexp")

        team_user = make_user("teamplayerexpuser")
        make_player(session, team_user, name="teamplayerexp", is_team_player=True)

        buffer = io.StringIO()
        player_to_csv(buffer, session)
        rows = {row[0]: row for row in read_csv(buffer)[1:]}

        self.assertEqual(rows["regularplayerexp"], ["regularplayerexp", "False", "False"])
        self.assertEqual(rows["guestplayerexp"], ["guestplayerexp", "True", "False"])
        self.assertEqual(rows["teamplayerexp"], ["teamplayerexp", "False", "True"])

    def test_players_from_other_sessions_are_excluded(self):
        session = make_session("exportplayersession3")
        other_session = make_session("exportplayersession4")
        user = make_user("otherplayerexp")
        make_player(other_session, user, name="otherplayerexp")

        buffer = io.StringIO()
        player_to_csv(buffer, session)
        rows = read_csv(buffer)
        self.assertEqual(rows[1:], [])


class GamesToCsvTests(TestCase):
    def test_header_row(self):
        session = make_session("exportgamesession1")
        buffer = io.StringIO()
        games_to_csv(buffer, session)
        rows = read_csv(buffer)
        self.assertEqual(
            rows[0],
            [
                "name", "url_tag", "playable", "visible", "results_visible", "needs_teams",
                "description", "illustration_path", "ordering_priority",
                "run_management_after_submit", "initial_view", "view_after_submit",
            ],
        )

    def test_game_fields_are_exported(self):
        session = make_session("exportgamesession2")
        game = make_game(
            session, url_tag="numb", name="Export Game", playable=True, visible=False,
            results_visible=True, needs_teams=False, description="A game",
            illustration_path="numbersgame/img/NumbersGame1.png", ordering_priority=3,
            run_management_after_submit=True, initial_view="index",
            view_after_submit="submit_answer",
        )
        buffer = io.StringIO()
        games_to_csv(buffer, session)
        rows = read_csv(buffer)
        self.assertEqual(
            rows[1],
            [
                "Export Game", "numb", "True", "False", "True", "False", "A game",
                "numbersgame/img/NumbersGame1.png", "3", "True", "index", "submit_answer",
            ],
        )

    def test_run_management_after_submit_none_is_blank(self):
        session = make_session("exportgamesession3")
        make_game(session, url_tag="numb", run_management_after_submit=None)
        buffer = io.StringIO()
        games_to_csv(buffer, session)
        rows = read_csv(buffer)
        self.assertEqual(rows[1][9], "")


class TeamToCsvTests(TestCase):
    def setUp(self):
        CustomUser.objects.create_user(
            username=TEAM_USER_USERNAME, password=TEAM_USER_PASSWORD
        )
        self.session = make_session("exportteamsession")
        self.game = make_game(self.session, url_tag="numb", needs_teams=True)

    def make_team(self, name, members):
        team_user = CustomUser.objects.get(username=TEAM_USER_USERNAME)
        team_player = Player.objects.create(
            user=team_user, name=f"TeamPlayer_{name}", session=self.session, is_team_player=True,
        )
        team = Team.objects.create(
            name=name, game=self.game, creator=members[0], team_player=team_player,
        )
        for member in members:
            team.players.add(member)
        return team

    def test_header_row_and_empty_body_with_no_teams(self):
        buffer = io.StringIO()
        team_to_csv(buffer, self.game)
        rows = read_csv(buffer)
        self.assertEqual(rows[0], ["name", "team_player_name", "player", "is_creator"])
        self.assertEqual(rows[1:], [])

    def test_one_row_per_member_with_creator_flagged(self):
        creator_user = make_user("teamcreatorexp")
        creator_player = make_player(self.session, creator_user, name="teamcreatorexp")
        member_user = make_user("teammemberexp")
        member_player = make_player(self.session, member_user, name="teammemberexp")
        team = self.make_team("ExportedTeam", [creator_player, member_player])

        buffer = io.StringIO()
        team_to_csv(buffer, self.game)
        rows = {row[2]: row for row in read_csv(buffer)[1:]}

        self.assertEqual(
            rows["teamcreatorexp"],
            ["ExportedTeam", team.team_player.name, "teamcreatorexp", "True"],
        )
        self.assertEqual(
            rows["teammemberexp"],
            ["ExportedTeam", team.team_player.name, "teammemberexp", "False"],
        )

    def test_teams_from_other_games_are_excluded(self):
        other_game = make_game(self.session, url_tag="othr", name="Other Game", needs_teams=True)
        creator_user = make_user("othergamecreator")
        creator_player = make_player(self.session, creator_user, name="othergamecreator")
        other_team_player = Player.objects.create(
            user=CustomUser.objects.get(username=TEAM_USER_USERNAME),
            name="TeamPlayer_OtherGameTeam", session=self.session, is_team_player=True,
        )
        Team.objects.create(
            name="OtherGameTeam", game=other_game, creator=creator_player,
            team_player=other_team_player,
        )

        buffer = io.StringIO()
        team_to_csv(buffer, self.game)
        rows = read_csv(buffer)
        self.assertEqual(rows[1:], [])
