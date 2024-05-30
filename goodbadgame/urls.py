from django.urls import re_path

from . import views

app_name = "goodbad"

urlpatterns = [
    re_path(r'^(?P<session_slug>[A-Za-z0-9_]+)/?$', views.goodbad_index, name='goodbad_index'),
    re_path(r'^(?P<session_slug>[A-Za-z0-9_]+)/(?P<player_slug>[A-Za-z0-9_-]+)/play/?$', views.goodbad_play,
            name='goodbad_play'),
    re_path(r'^(?P<session_slug>[A-Za-z0-9_]+)/(?P<player_slug>[A-Za-z0-9_-]+)/result/?$',
            views.goodbad_result, name='goodbad_result'),
    re_path(r'^(?P<session_slug>[A-Za-z0-9_]+)/(?P<player_slug>[A-Za-z0-9_-]+)/detailedresult/?$',
            views.goodbad_result, kwargs={'detailed': True}, name='goodbad_detailed_result'),
    re_path(r'^(?P<session_slug>[A-Za-z0-9_]+)/result/?$', views.goodbad_detailed_result_all,
            name='goodbad_result_all'),
]

