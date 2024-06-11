import re

from django.urls import path

from core.games import INSTALLED_GAMES
from . import views


app_name = "core"
urlpatterns = [
    path("", views.index, name="index"),
    path("createsession/", views.create_session, name="create_session"),
    path("message/", views.message, name="message"),
    path("logout/", views.logout_user, name="logout"),
    path("user/<int:user_id>/", views.user_profile, name="user_profile"),
    path("user/<int:user_id>/password/", views.change_password, name="change_password"),
    path(
        "<slug:session_url_tag>/",
        views.session_portal,
        name="session_portal",
    ),
    path(
        "<slug:session_url_tag>/forcedlogout/",
        views.force_player_logout,
        name="force_player_logout",
    ),
    path(
        "<slug:session_url_tag>/home/",
        views.session_home,
        name="session_home",
    ),
    path("<slug:session_url_tag>/admin/", views.session_admin, name="session_admin"),
    path(
        "<slug:session_url_tag>/admin/games/",
        views.session_admin_games,
        name="session_admin_games",
    ),
    path(
        "<slug:session_url_tag>/admin/games/<slug:game_url_tag>/",
        views.session_admin_games_settings,
        name="session_admin_games_settings",
    ),
    path(
        "<slug:session_url_tag>/admin/games/<slug:game_url_tag>/answers/",
        views.session_admin_games_answers,
        name="session_admin_games_answers",
    ),
    path(
        "<slug:session_url_tag>/admin/games/<slug:game_url_tag>/answers/export/",
        views.session_admin_games_answers_export,
        name="session_admin_games_answers_export",
    ),
    path(
        "<slug:session_url_tag>/admin/games/<slug:game_url_tag>/teams/",
        views.session_admin_games_teams,
        name="session_admin_games_teams",
    ),
    path(
        "<slug:session_url_tag>/admin/games/<slug:game_url_tag>/teams/export/",
        views.session_admin_games_teams_export,
        name="session_admin_games_teams_export",
    ),
    path(
        "<slug:session_url_tag>/admin/players/",
        views.session_admin_players,
        name="session_admin_players",
    ),
    path(
        "<slug:session_url_tag>/admin/players/export",
        views.session_admin_players_export,
        name="session_admin_players_export",
    ),
    path(
        "<slug:session_url_tag>/admin/player/<int:player_user_id>/password/",
        views.session_admin_player_password,
        name="session_admin_player_password",
    ),
]

for game_config in INSTALLED_GAMES:
    urlpatterns += [
        path(
            "<slug:session_url_tag>/"
            + re.escape(str(game_config.url_tag))
            + r"/<slug:game_url_tag>/team",
            views.create_or_join_team,
            name=game_config.url_tag + "_team",
        ),
        path(
            "<slug:session_url_tag>/"
            + re.escape(str(game_config.url_tag))
            + r"/<slug:game_url_tag>/admin/visibility_toggle",
            views.game_visibility_toggle,
            name=game_config.url_tag + "_visibility_toggle",
            kwargs={"game_type": game_config.name},
        ),
        path(
            "<slug:session_url_tag>/"
            + re.escape(str(game_config.url_tag))
            + r"/<slug:game_url_tag>/admin/play_toggle",
            views.game_play_toggle,
            name=game_config.url_tag + "_play_toggle",
            kwargs={"game_type": game_config.name},
        ),
        path(
            "<slug:session_url_tag>/"
            + re.escape(str(game_config.url_tag))
            + r"/<slug:game_url_tag>/admin/result_toggle",
            views.game_result_toggle,
            name=game_config.url_tag + "_result_toggle",
            kwargs={"game_type": game_config.name},
        ),
        path(
            "<slug:session_url_tag>/"
            + re.escape(str(game_config.url_tag))
            + r"/<slug:game_url_tag>/admin/run_management",
            views.game_run_management_cmds,
            name=game_config.url_tag + "_run_management",
            kwargs={"game_type": game_config.name},
        ),
    ]
