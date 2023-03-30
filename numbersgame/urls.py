from django.urls import re_path

from . import views

app_name = 'numbers_game'
urlpatterns = [
    re_path(r'^$', views.index, name='index'),
    re_path(r'^answer[/]$', views.submit_answer, name='submit_answer'),
    re_path(r'^results[/]$', views.results, name='results'),
]
