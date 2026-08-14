"""Shared factory helpers for core tests."""
from core.models import CustomUser, Session, Player, Game


def make_session(url_tag="testsession", **kwargs):
    kwargs.setdefault("name", url_tag)
    kwargs.setdefault("long_name", url_tag)
    return Session.objects.create(url_tag=url_tag, **kwargs)


def make_user(username, *, is_player=False, is_staff=False, password="pw"):
    return CustomUser.objects.create_user(
        username=username, password=password, is_player=is_player, is_staff=is_staff,
    )


def make_game(session, *, game_type="numbersgame", url_tag="numb", name="Numbers", **kwargs):
    # initial_view/view_after_submit default to "index" (a real URL name for every game app
    # here) since templates that link to the game (e.g. session_admin_games.html) reverse a
    # URL from them and would raise NoReverseMatch if left blank.
    kwargs.setdefault("initial_view", "index")
    kwargs.setdefault("view_after_submit", "index")
    return Game.objects.create(
        game_type=game_type, name=name, url_tag=url_tag, session=session, **kwargs
    )


def make_player(session, user, *, name=None, is_team_player=False):
    return Player.objects.create(
        user=user, name=name or user.username, session=session, is_team_player=is_team_player,
    )
