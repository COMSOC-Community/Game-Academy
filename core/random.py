import random
import string

from django.contrib.auth.hashers import make_password

from core.constants import RANDOM_PLAYERNAME_PREFIX
from core.models import CustomUser, Player


def random_user():
    player_name = RANDOM_PLAYERNAME_PREFIX + "a"
    while CustomUser.objects.filter(username=player_name).exists() or Player.objects.filter(
            name=player_name).exists():
        player_name = RANDOM_PLAYERNAME_PREFIX + ''.join(
            random.choices(string.ascii_letters + string.digits, k=15))
    return CustomUser(
        username=player_name,
        password=make_password(None),
        is_player=True
    )


def create_random_players(session, num_players):
    new_users = [random_user() for _ in range(num_players)]
    new_users = CustomUser.objects.bulk_create(new_users)
    new_players = []
    for user in new_users:
        new_players.append(
            Player.objects.create(
                user=user,
                name=user.username,
                session=session,
            )
        )
    return Player.objects.bulk_create(new_players)
