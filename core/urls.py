import re

from django.urls import re_path, include

from gameserver.games import INSTALLED_GAMES_SETTING
from . import views

app_name = "core"
urlpatterns = [
    re_path(r"^$", views.index, name="index"),
    re_path(r"^logout[/]$", views.logout_user, name="logout"),
    re_path(r"^createsession[/]", views.create_session, name="create_session"),
    re_path(
        r"^session/(?P<session_slug_name>[\w-]+)[/]?$",
        views.session_index,
        name="session_portal",
    ),
    re_path(
        r"^session/(?P<session_slug_name>[\w-]+)/home[/]?$",
        views.session_home,
        name="session_home",
    ),
    re_path(
        r"^session/(?P<session_slug_name>[\w-]+)/admin[/]?$",
        views.session_admin,
        name="session_admin",
    ),
]

for game_setting in INSTALLED_GAMES_SETTING.values():
    urlpatterns.append(
        re_path(
            r"^session/(?P<session_slug_name>[\w-]+)/"
            + re.escape(str(game_setting.url_tag))
            + r"/(?P<game_url_tag>[\w-]+)/team",
            views.team,
            name="team_" + game_setting.package_url_namespace,
        )
    )
