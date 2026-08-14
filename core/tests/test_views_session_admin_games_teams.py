from django.test import TestCase
from django.urls import reverse

from core.constants import TEAM_USER_USERNAME, TEAM_USER_PASSWORD
from core.models import CustomUser, Player, Team
from core.tests.helpers import make_session, make_user, make_game, make_player


class SessionAdminGamesTeamsViewTests(TestCase):
    def setUp(self):
        CustomUser.objects.create_user(
            username=TEAM_USER_USERNAME, password=TEAM_USER_PASSWORD
        )
        self.session = make_session("gteamsadminsession", visible=True)
        self.game = make_game(
            self.session, url_tag="numb", visible=True, needs_teams=True
        )
        self.admin = make_user("gteamsadmin")
        self.session.admins.add(self.admin)

    def url(self):
        return reverse(
            "core:session_admin_games_teams", args=(self.session.url_tag, self.game.url_tag)
        )

    def make_team(self, name, *, is_public=True):
        creator_user = make_user(f"creator_{name}")
        creator_player = make_player(self.session, creator_user, name=f"creator_{name}")
        team_user = CustomUser.objects.get(username=TEAM_USER_USERNAME)
        team_player = Player.objects.create(
            user=team_user, name=f"TeamPlayer_{name}", session=self.session, is_team_player=True,
        )
        team = Team.objects.create(
            name=name, game=self.game, creator=creator_player, is_public=is_public,
            team_player=team_player,
        )
        team.players.add(creator_player)
        return team

    def test_non_admin_is_blocked(self):
        make_user("gteamsintruder")
        self.client.login(username="gteamsintruder", password="pw")
        response = self.client.get(self.url())
        self.assertEqual(response.status_code, 404)

    def test_admin_can_view_with_no_teams(self):
        self.client.login(username="gteamsadmin", password="pw")
        response = self.client.get(self.url())
        self.assertEqual(response.status_code, 200)
        self.assertEqual(list(response.context["teams"]), [])

    def test_admin_view_lists_existing_teams(self):
        team = self.make_team("TeamOne")
        self.client.login(username="gteamsadmin", password="pw")
        response = self.client.get(self.url())
        self.assertIn(team, response.context["teams"])

    def test_delete_single_team(self):
        team = self.make_team("TeamTwo")
        self.client.login(username="gteamsadmin", password="pw")
        response = self.client.post(
            self.url(), {"delete_team_form": "1", "remove_team_id": str(team.id)}
        )
        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.context["deleted_team_name"], "TeamTwo")
        self.assertFalse(Team.objects.filter(pk=team.pk).exists())

    def test_delete_all_teams(self):
        self.make_team("TeamThree")
        self.make_team("TeamFour")
        self.client.login(username="gteamsadmin", password="pw")
        response = self.client.post(self.url(), {"delete_all_teams_form": "1"})
        self.assertEqual(response.status_code, 200)
        self.assertTrue(response.context["all_teams_deleted"])
        self.assertEqual(Team.objects.filter(game=self.game).count(), 0)

    def test_teams_export_returns_csv(self):
        self.make_team("TeamFive")
        self.client.login(username="gteamsadmin", password="pw")
        response = self.client.get(
            reverse(
                "core:session_admin_games_teams_export",
                args=(self.session.url_tag, self.game.url_tag),
            )
        )
        self.assertEqual(response.status_code, 200)
        self.assertEqual(response["Content-Type"], "text/csv")

    def test_teams_export_blocked_for_non_admin(self):
        make_user("gteamsexportintruder")
        self.client.login(username="gteamsexportintruder", password="pw")
        response = self.client.get(
            reverse(
                "core:session_admin_games_teams_export",
                args=(self.session.url_tag, self.game.url_tag),
            )
        )
        self.assertEqual(response.status_code, 404)
