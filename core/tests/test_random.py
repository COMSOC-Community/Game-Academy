from django.test import TestCase

from core.constants import RANDOM_PLAYERNAME_PREFIX, TEAM_USER_USERNAME
from core.models import CustomUser, Player, Team
from core.random import random_user_names, create_random_players, create_random_teams
from core.tests.helpers import make_session, make_game


class RandomUserNamesTests(TestCase):
    def test_first_name_uses_bare_prefix_when_no_collision(self):
        names = random_user_names(1)
        self.assertEqual(names, [f"{RANDOM_PLAYERNAME_PREFIX}_"])

    def test_generates_the_requested_count_all_unique(self):
        names = random_user_names(5)
        self.assertEqual(len(names), 5)
        self.assertEqual(len(set(names)), 5)

    def test_only_first_name_can_use_the_bare_prefix(self):
        names = random_user_names(3)
        self.assertEqual(names[0], f"{RANDOM_PLAYERNAME_PREFIX}_")
        for name in names[1:]:
            self.assertNotEqual(name, f"{RANDOM_PLAYERNAME_PREFIX}_")
            self.assertTrue(name.startswith(f"{RANDOM_PLAYERNAME_PREFIX}_"))

    def test_avoids_collision_with_existing_usernames(self):
        CustomUser.objects.create_user(
            username=f"{RANDOM_PLAYERNAME_PREFIX}_", password="pw"
        )
        names = random_user_names(1)
        self.assertNotEqual(names[0], f"{RANDOM_PLAYERNAME_PREFIX}_")

    def test_avoids_collision_with_existing_player_names(self):
        session = make_session("randomnamecollision")
        user = CustomUser.objects.create_user(username="someuser", password="pw")
        Player.objects.create(
            user=user, name=f"{RANDOM_PLAYERNAME_PREFIX}_", session=session
        )
        names = random_user_names(1)
        self.assertNotEqual(names[0], f"{RANDOM_PLAYERNAME_PREFIX}_")


class CreateRandomPlayersTests(TestCase):
    def test_creates_the_requested_number_of_players(self):
        session = make_session("createrandomplayerssession")
        players = create_random_players(session, 4)
        self.assertEqual(len(players), 4)
        self.assertEqual(
            Player.objects.filter(session=session).count(), 4
        )

    def test_players_are_flagged_as_random_and_restricted(self):
        session = make_session("createrandomplayerssession2")
        players = create_random_players(session, 1)
        player = players[0]
        self.assertTrue(player.user.is_random_player)
        self.assertTrue(player.user.is_player)

    def test_player_name_matches_username(self):
        session = make_session("createrandomplayerssession3")
        players = create_random_players(session, 1)
        self.assertEqual(players[0].name, players[0].user.username)

    def test_created_users_have_unusable_passwords(self):
        session = make_session("createrandomplayerssession4")
        players = create_random_players(session, 1)
        self.assertFalse(players[0].user.has_usable_password())


class CreateRandomTeamsTests(TestCase):
    def setUp(self):
        CustomUser.objects.create_user(username=TEAM_USER_USERNAME, password="pw")
        self.session = make_session("createrandomteamssession")
        self.game = make_game(self.session, url_tag="numb", needs_teams=True)

    def test_creates_the_requested_number_of_teams(self):
        teams = create_random_teams(self.session, self.game, 3)
        self.assertEqual(len(teams), 3)
        self.assertEqual(Team.objects.filter(game=self.game).count(), 3)

    def test_each_team_has_a_random_player_as_creator_and_member(self):
        teams = create_random_teams(self.session, self.game, 1)
        team = teams[0]
        self.assertTrue(team.creator.user.is_random_player)
        self.assertIn(team.creator, team.players.all())

    def test_team_player_is_linked_to_the_shared_team_user_account(self):
        teams = create_random_teams(self.session, self.game, 1)
        team = teams[0]
        self.assertEqual(team.team_player.user.username, TEAM_USER_USERNAME)
        self.assertTrue(team.team_player.is_team_player)

    def test_raises_when_team_user_account_is_missing(self):
        CustomUser.objects.filter(username=TEAM_USER_USERNAME).delete()
        with self.assertRaises(CustomUser.DoesNotExist):
            create_random_teams(self.session, self.game, 1)
