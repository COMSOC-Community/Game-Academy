import re

from django.urls import re_path, include

from gameserver.games import INSTALLED_GAMES_SETTING
from . import views

app_name = "core"
urlpatterns = [
    re_path(r"^$", views.index, name="index"),
    re_path(r"^logout[/]$", views.logout_user, name="logout"),
    re_path(r"^password[/]$", views.change_password, name="change_password"),
    re_path(r"^createsession[/]", views.create_session, name="create_session"),
    re_path(r"^message[/]", views.message, name="message"),
    re_path(
        r"^s/(?P<session_url_tag>[\w-]+)[/]?$",
        views.session_portal,
        name="session_portal",
    ),
    re_path(
        r"^s/(?P<session_url_tag>[\w-]+)/forcedlogout[/]$",
        views.force_player_logout,
        name="force_player_logout",
    ),
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
    urlpatterns += [
        re_path(
            r"^s/(?P<session_url_tag>[\w-]+)/"
            + re.escape(str(game_setting.url_tag))
            + r"/(?P<game_url_tag>[\w-]+)/team",
            views.team,
            name=game_setting.url_tag + "_team",
        ),
        re_path(
            r"^s/(?P<session_url_tag>[\w-]+)/"
            + re.escape(str(game_setting.url_tag))
            + r"/(?P<game_url_tag>[\w-]+)/admin/play_toggle",
            views.game_play_toggle,
            name=game_setting.url_tag + "_play_toggle",
            kwargs={"game_type": game_setting.name},
        ),
        re_path(
            r"^s/(?P<session_url_tag>[\w-]+)/"
            + re.escape(str(game_setting.url_tag))
            + r"/(?P<game_url_tag>[\w-]+)/admin/result_toggle",
            views.game_result_toggle,
            name=game_setting.url_tag + "_result_toggle",
            kwargs={"game_type": game_setting.name},
        ),
        re_path(
            r"^s/(?P<session_url_tag>[\w-]+)/"
            + re.escape(str(game_setting.url_tag))
            + r"/(?P<game_url_tag>[\w-]+)/admin/run_management",
            views.game_run_management_cmds,
            name=game_setting.url_tag + "_run_management",
            kwargs={"game_type": game_setting.name},
        ),
    ]
