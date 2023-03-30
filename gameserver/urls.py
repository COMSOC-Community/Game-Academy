from django.contrib import admin
from django.urls import path, re_path, include
from django.conf.urls import handler400, handler403, handler404, handler500

from core.views import error_400_view, error_403_view, error_404_view, error_500_view

import re

from gameserver.games import INSTALLED_GAMES_SETTING

handler400 = error_400_view
handler403 = error_403_view
handler404 = error_404_view
handler500 = error_500_view

urlpatterns = [
    path('', include('core.urls')),
    re_path(r'^admin/', admin.site.urls),
]

for game_setting in INSTALLED_GAMES_SETTING.values():
    urlpatterns.append(re_path(r'^session/(?P<session_slug_name>[\w-]+)/' + re.escape(str(game_setting.url_tag)) +
                               r'/(?P<game_url_tag>[\w-]+)/', include(str(game_setting.package_name) + '.urls',
                                                                      namespace=game_setting.package_url_namespace)))
