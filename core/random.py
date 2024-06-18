import random
import string

from django.contrib.auth.hashers import make_password

from core.constants import RANDOM_PLAYERNAME_PREFIX, TEAM_USER_USERNAME
from core.models import CustomUser, Player, Team


def random_user_names(num_users):
    res = []
    db_user_names = CustomUser.objects.all().values_list("username", flat=True)
    db_player_names = Player.objects.all().values_list("name", flat=True)
    for _ in range(num_users):
        player_name = RANDOM_PLAYERNAME_PREFIX + "_"
        while (
            player_name in res
            or player_name in db_player_names
            or player_name in db_user_names
        ):
            player_name = (
                RANDOM_PLAYERNAME_PREFIX
                + "_"
                + "".join(random.choices(string.ascii_letters + string.digits, k=20))
            )
        res.append(player_name)
    return res


def create_random_players(session, num_players):
    new_users = [
        CustomUser(username=name, password=make_password(None), is_player=True)
        for name in random_user_names(num_players)
    ]
    new_users = CustomUser.objects.bulk_create(new_users)
    new_players = []
    for user in new_users:
        new_players.append(
            Player(
                user=user,
                name=user.username,
                session=session,
            )
        )
    return Player.objects.bulk_create(new_players)


def create_random_teams(session, game, num_teams):
    players = create_random_players(session, num_teams)
    team_player_user = CustomUser.objects.get(username=TEAM_USER_USERNAME)
    team_players = []
    for player in players:
        team_players.append(
            Player(
                user=team_player_user,
                name="TEAMPLAYER_" + player.name,
                session=session,
                is_team_player=True,
            )
        )
    team_players = Player.objects.bulk_create(team_players)
    teams = []
    for i, player in enumerate(players):
        teams.append(
            Team(
                name="TEAM_" + player.name,
                game=game,
                creator=player,
                team_player=team_players[i],
            )
        )
    teams = Team.objects.bulk_create(teams)
    for i, player in enumerate(players):
        team = teams[i]
        team.players.add(player)
        team.save()
    return teams
