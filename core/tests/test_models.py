from unittest import mock

from django.db import IntegrityError, transaction
from django.test import TestCase

from core.models import CustomUser, Session, Player, Game, Team
from core.tests.helpers import make_session, make_user, make_game


class CustomUserTests(TestCase):
    def test_str_returns_username(self):
        user = make_user("alice")
        self.assertEqual(str(user), "alice")

    def test_display_name_for_regular_user_is_username(self):
        user = make_user("alice")
        self.assertEqual(user.display_name(), "alice")

    def test_display_name_for_player_restricted_user_is_player_name(self):
        session = make_session()
        user = make_user("Player_testsession_bob", is_player=True)
        Player.objects.create(user=user, name="bob", session=session)
        self.assertEqual(user.display_name(), "bob")


class SessionTests(TestCase):
    def test_str_combines_url_tag_and_name(self):
        session = Session.objects.create(
            url_tag="mytag", name="My Session", long_name="My Long Session Name",
        )
        self.assertEqual(str(session), "mytag - My Session")


class PlayerTests(TestCase):
    def setUp(self):
        self.session = make_session()

    def test_str_combines_session_name_and_player_name(self):
        user = make_user("alice")
        player = Player.objects.create(user=user, name="alice", session=self.session)
        self.assertEqual(str(player), f"[{self.session.name}] alice")

    def test_display_name_for_regular_player_is_its_name(self):
        user = make_user("alice")
        player = Player.objects.create(user=user, name="alice", session=self.session)
        self.assertEqual(player.display_name(), "alice")

    def test_display_name_for_team_player_is_team_name(self):
        team_user = make_user("TeamUser1")
        team_player = Player.objects.create(
            user=team_user, name="sometimplicitname", session=self.session, is_team_player=True,
        )
        creator_user = make_user("creator")
        creator_player = Player.objects.create(
            user=creator_user, name="creator", session=self.session,
        )
        game = make_game(self.session)
        Team.objects.create(
            name="Team Rocket", game=game, creator=creator_player, team_player=team_player,
        )
        self.assertEqual(team_player.display_name(), "Team Rocket")

    def test_display_name_for_team_player_without_team_falls_back_to_name(self):
        team_user = make_user("TeamUser2")
        team_player = Player.objects.create(
            user=team_user, name="orphan_team_player", session=self.session, is_team_player=True,
        )
        # No Team object points to this player as its team_player.
        self.assertEqual(team_player.display_name(), "orphan_team_player")

    def test_name_must_be_unique_within_a_session(self):
        user1 = make_user("alice")
        user2 = make_user("alice2")
        Player.objects.create(user=user1, name="alice", session=self.session)
        with self.assertRaises(IntegrityError):
            with transaction.atomic():
                Player.objects.create(user=user2, name="alice", session=self.session)

    def test_same_name_allowed_in_different_sessions(self):
        other_session = make_session("othersession")
        user1 = make_user("alice")
        user2 = make_user("alice2")
        Player.objects.create(user=user1, name="alice", session=self.session)
        # Should not raise: same player name, different session.
        Player.objects.create(user=user2, name="alice", session=other_session)


class PlayerDeleteSignalTests(TestCase):
    """Tests for delete_user_after_player: deleting a session-restricted player should
    delete the underlying user, but team players and non-restricted users must be spared."""

    def setUp(self):
        self.session = make_session()

    def test_deleting_restricted_player_deletes_underlying_user(self):
        user = make_user("Player_testsession_alice", is_player=True)
        player = Player.objects.create(user=user, name="alice", session=self.session)
        player.delete()
        self.assertFalse(CustomUser.objects.filter(pk=user.pk).exists())

    def test_deleting_team_player_does_not_delete_its_user(self):
        user = make_user("TeamUser3", is_player=True)
        player = Player.objects.create(
            user=user, name="teamplayer", session=self.session, is_team_player=True,
        )
        player.delete()
        self.assertTrue(CustomUser.objects.filter(pk=user.pk).exists())

    def test_deleting_player_of_non_restricted_user_does_not_delete_user(self):
        user = make_user("global_user", is_player=False)
        player = Player.objects.create(user=user, name="alice", session=self.session)
        player.delete()
        self.assertTrue(CustomUser.objects.filter(pk=user.pk).exists())

    def test_deleting_session_cascades_to_restricted_users(self):
        user = make_user("Player_testsession_alice", is_player=True)
        Player.objects.create(user=user, name="alice", session=self.session)
        self.session.delete()
        self.assertFalse(CustomUser.objects.filter(pk=user.pk).exists())


class TeamTests(TestCase):
    def setUp(self):
        self.session = make_session()
        self.game = make_game(self.session)
        creator_user = make_user("creator")
        self.creator_player = Player.objects.create(
            user=creator_user, name="creator", session=self.session,
        )
        team_user = make_user("TeamUser4")
        self.team_player = Player.objects.create(
            user=team_user, name="teamplayerforstr", session=self.session, is_team_player=True,
        )

    def test_str_combines_session_game_and_team_name(self):
        team = Team.objects.create(
            name="Team Rocket", game=self.game, creator=self.creator_player,
            team_player=self.team_player,
        )
        self.assertEqual(
            str(team), f"[{self.session}] {self.game.name} - Team Rocket"
        )

    def test_name_must_be_unique_within_a_game(self):
        Team.objects.create(
            name="Team Rocket", game=self.game, creator=self.creator_player,
            team_player=self.team_player,
        )
        other_team_user = make_user("TeamUser5")
        other_team_player = Player.objects.create(
            user=other_team_user, name="otherteamplayer", session=self.session, is_team_player=True,
        )
        with self.assertRaises(IntegrityError):
            with transaction.atomic():
                Team.objects.create(
                    name="Team Rocket", game=self.game, creator=self.creator_player,
                    team_player=other_team_player,
                )

    def test_deleting_team_deletes_its_team_player(self):
        team = Team.objects.create(
            name="Team Rocket", game=self.game, creator=self.creator_player,
            team_player=self.team_player,
        )
        team_player_pk = self.team_player.pk
        team.delete()
        self.assertFalse(Player.objects.filter(pk=team_player_pk).exists())


class GameTests(TestCase):
    def setUp(self):
        self.session = make_session()

    def test_str_combines_session_and_game_name(self):
        game = make_game(self.session, name="Numbers Game")
        self.assertEqual(str(game), f"[{self.session}] Numbers Game")

    def test_game_config_resolves_registered_game_type(self):
        game = make_game(self.session, game_type="numbersgame")
        config = game.game_config()
        self.assertEqual(config.name, "numbersgame")

    def test_game_config_is_cached_after_first_lookup(self):
        game = make_game(self.session, game_type="numbersgame")
        first = game.game_config()
        # Blank out the registry: if the method looked it up again it would raise.
        with mock.patch("core.models.INSTALLED_GAMES", []):
            second = game.game_config()
        self.assertIs(first, second)

    def test_game_config_raises_for_unregistered_game_type(self):
        game = make_game(self.session, game_type="not_a_real_game_type")
        with self.assertRaises(ValueError):
            game.game_config()

    def test_all_url_names_lists_the_game_apps_urls(self):
        game = make_game(self.session, game_type="numbersgame")
        self.assertEqual(
            set(game.all_url_names()), {"index", "submit_answer", "global_results"}
        )

    def test_url_tag_must_be_unique_within_a_session(self):
        make_game(self.session, url_tag="numb", name="First Numbers Game")
        with self.assertRaises(IntegrityError):
            with transaction.atomic():
                make_game(self.session, url_tag="numb", name="Second Numbers Game")

    def test_name_must_be_unique_within_a_session(self):
        make_game(self.session, url_tag="numb1", name="Same Name")
        with self.assertRaises(IntegrityError):
            with transaction.atomic():
                make_game(self.session, url_tag="numb2", name="Same Name")
