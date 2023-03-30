from django.urls import re_path

from . import views

app_name = 'core'
urlpatterns = [
    re_path(r'^$', views.index, name='index'),
    re_path(r'^logout[/]$', views.logout_user, name='logout'),
    re_path(r'^createsession[/]', views.create_session, name='create_session'),
    re_path(r'^session/(?P<session_slug_name>[\w-]+)[/]?$', views.session_index, name='index_session'),
    re_path(r'^session/(?P<session_slug_name>[\w-]+)/home[/]?$', views.session_home, name='session_home'),
    re_path(r'^session/(?P<session_slug_name>[\w-]+)/admin[/]?$', views.session_admin, name='session_admin'),
]

