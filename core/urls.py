import re

from django.urls import re_path, include

from gameserver.games import INSTALLED_GAMES_SETTING
from . import views

app_name = "core"
urlpatterns = [
    re_path(r"^$", views.index, name="index"),
    re_path(r"^logout[/]$", views.logout_user, name="logout"),
    re_path(r"^createsession[/]", views.create_session, name="create_session"),
    re_path(r"^message[/]", views.message, name="message"),
    re_path(
        r"^s/(?P<session_url_tag>[\w-]+)[/]?$",
        views.session_portal,
        name="session_portal",
    ),
    re_path(r"^s/(?P<session_url_tag>[\w-]+)/forcedlogout[/]$", views.force_player_logout, name="force_player_logout"),
    re_path(
        r"^s/(?P<session_url_tag>[\w-]+)/home[/]?$",
        views.session_home,
        name="session_home",
    ),
    re_path(
        r"^s/(?P<session_url_tag>[\w-]+)/admin[/]?$",
        views.session_admin,
        name="session_admin",
    ),
    re_path(
        r"^s/(?P<session_url_tag>[\w-]+)/admin/games[/]?$",
        views.session_admin_games,
        name="session_admin_games",
    ),
    re_path(
        r"^s/(?P<session_url_tag>[\w-]+)/admin/players[/]?$",
        views.session_admin_players,
        name="session_admin_players",
    ),
    re_path(
        r"^s/(?P<session_url_tag>[\w-]+)/admin/player/(?P<player_name>[\w-]+)/password[/]?$",
        views.session_admin_player_password,
        name="session_admin_player_password",
    ),
]

for game_setting in INSTALLED_GAMES_SETTING.values():
    urlpatterns.append(
        re_path(
            r"^s/(?P<session_url_tag>[\w-]+)/"
            + re.escape(str(game_setting.url_tag))
            + r"/(?P<game_url_tag>[\w-]+)/team",
            views.team,
            name="team_" + game_setting.package_url_namespace,
        )
    )
