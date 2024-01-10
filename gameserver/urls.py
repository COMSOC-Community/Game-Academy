from django.contrib import admin
from django.urls import path, re_path, include

from core.views import error_400_view, error_403_view, error_404_view, error_500_view

import re

from core.games import INSTALLED_GAMES

handler400 = error_400_view
handler403 = error_403_view
handler404 = error_404_view
handler500 = error_500_view

urlpatterns = [
    path("", include("core.urls")),
    re_path(r"^admin/", admin.site.urls),
]

for game_config in INSTALLED_GAMES:
    urlpatterns.append(
        re_path(
            r"^s/(?P<session_url_tag>[\w-]+)/"
            + re.escape(str(game_config.url_tag))
            + r"/(?P<game_url_tag>[\w-]+)/",
            include(
                str(game_config.package_name) + ".urls",
                namespace=game_config.url_namespace,
            ),
        )
    )
