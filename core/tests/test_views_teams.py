from django.test import TestCase
from django.urls import reverse

from core.constants import TEAM_USER_USERNAME, TEAM_USER_PASSWORD
from core.models import CustomUser, Player, Team
from core.tests.helpers import make_session, make_user, make_game, make_player


class CreateOrJoinTeamViewTests(TestCase):
    def setUp(self):
        CustomUser.objects.create_user(
            username=TEAM_USER_USERNAME, password=TEAM_USER_PASSWORD
        )
        self.session = make_session("teamsession", visible=True)
        self.game = make_game(
            self.session, url_tag="numb", needs_teams=True, playable=True, visible=True,
        )
        self.admin = make_user("teamadmin")
        self.session.admins.add(self.admin)

    def url(self):
        return reverse(
            "core:numbers_team", args=(self.session.url_tag, self.game.url_tag)
        )

    def make_extra_team(self, creator_player, *, name="ExistingTeam", is_public=True):
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

    def test_game_without_needs_teams_is_404(self):
        other_game = make_game(
            self.session, url_tag="notm", name="Not A Team Game", needs_teams=False
        )
        make_user("someuser")
        self.client.login(username="someuser", password="pw")
        response = self.client.get(
            reverse("core:numbers_team", args=(self.session.url_tag, other_game.url_tag))
        )
        self.assertEqual(response.status_code, 404)

    def test_non_playable_game_blocks_non_admin(self):
        self.game.playable = False
        self.game.save()
        user = make_user("blockeduser")
        make_player(self.session, user, name="blockeduser")
        self.client.login(username="blockeduser", password="pw")
        response = self.client.get(self.url())
        self.assertEqual(response.status_code, 404)

    def test_player_without_team_sees_create_and_join_forms(self):
        user = make_user("noteamplayer")
        make_player(self.session, user, name="noteamplayer")
        self.client.login(username="noteamplayer", password="pw")
        response = self.client.get(self.url())
        self.assertEqual(response.status_code, 200)
        self.assertIn("create_team_form", response.context)
        self.assertIn("join_private_team_form", response.context)
        # No public teams exist yet.
        self.assertIsNone(response.context["join_public_team_form"])

    def test_create_team_creates_it_and_adds_creator(self):
        user = make_user("creatorplayer")
        player = make_player(self.session, user, name="creatorplayer")
        self.client.login(username="creatorplayer", password="pw")
        response = self.client.post(
            self.url(), {"create_team_form": "1", "name": "Team Alpha", "is_public": "on"}
        )
        self.assertEqual(response.status_code, 200)
        team = Team.objects.get(game=self.game, name="Team Alpha")
        self.assertEqual(response.context["created_team"], team)
        self.assertEqual(team.creator, player)
        self.assertIn(player, team.players.all())

    def test_create_team_duplicate_name_shows_error(self):
        other_user = make_user("otherplayer")
        other_player = make_player(self.session, other_user, name="otherplayer")
        self.make_extra_team(other_player, name="Taken")

        user = make_user("creatorplayer2")
        make_player(self.session, user, name="creatorplayer2")
        self.client.login(username="creatorplayer2", password="pw")
        response = self.client.post(
            self.url(), {"create_team_form": "1", "name": "Taken", "is_public": "on"}
        )
        self.assertEqual(response.status_code, 200)
        self.assertTrue(response.context["create_team_form"].errors)

    def test_join_public_team_adds_the_player(self):
        creator_user = make_user("publicteamcreator")
        creator_player = make_player(self.session, creator_user, name="publicteamcreator")
        team = self.make_extra_team(creator_player, name="PublicTeam", is_public=True)

        joiner_user = make_user("publicteamjoiner")
        joiner_player = make_player(self.session, joiner_user, name="publicteamjoiner")
        self.client.login(username="publicteamjoiner", password="pw")
        response = self.client.post(
            self.url(), {"join_public_team_form": "1", "team": str(team.id)}
        )
        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.context["joined_team_name"], "PublicTeam")
        self.assertIn(joiner_player, team.players.all())

    def test_join_private_team_by_name(self):
        creator_user = make_user("privateteamcreator")
        creator_player = make_player(self.session, creator_user, name="privateteamcreator")
        team = self.make_extra_team(creator_player, name="PrivateTeam", is_public=False)

        joiner_user = make_user("privateteamjoiner")
        joiner_player = make_player(self.session, joiner_user, name="privateteamjoiner")
        self.client.login(username="privateteamjoiner", password="pw")
        response = self.client.post(
            self.url(), {"join_private_team_form": "1", "name": "PrivateTeam"}
        )
        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.context["joined_team_name"], "PrivateTeam")
        self.assertIn(joiner_player, team.players.all())

    def test_join_private_team_unknown_name_shows_error(self):
        user = make_user("privatejoinerbad")
        make_player(self.session, user, name="privatejoinerbad")
        self.client.login(username="privatejoinerbad", password="pw")
        response = self.client.post(
            self.url(), {"join_private_team_form": "1", "name": "NoSuchTeam"}
        )
        self.assertEqual(response.status_code, 200)
        self.assertTrue(response.context["join_private_team_form"].errors)

    def test_player_already_in_a_team_sees_no_team_forms(self):
        user = make_user("alreadyinteam")
        player = make_player(self.session, user, name="alreadyinteam")
        self.make_extra_team(player, name="MyTeam", is_public=True)

        self.client.login(username="alreadyinteam", password="pw")
        response = self.client.get(self.url())
        self.assertEqual(response.status_code, 200)
        self.assertNotIn("create_team_form", response.context)

    def test_admin_without_player_profile_can_still_view_page(self):
        self.client.login(username="teamadmin", password="pw")
        response = self.client.get(self.url())
        self.assertEqual(response.status_code, 200)
        self.assertNotIn("create_team_form", response.context)

    def test_post_without_known_marker_is_404(self):
        user = make_user("badmarkeruser")
        make_player(self.session, user, name="badmarkeruser")
        self.client.login(username="badmarkeruser", password="pw")
        response = self.client.post(self.url(), {"unknown_marker": "1"})
        self.assertEqual(response.status_code, 404)
