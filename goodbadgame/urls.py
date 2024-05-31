from django.urls import path

from . import views
from .apps import URL_NAMESPACE

app_name = URL_NAMESPACE
urlpatterns = [
    path("", views.index, name="index"),
    path("answer/", views.submit_answer, name="submit_answer"),
    path("playerresults/", views.player_results, name="player_results"),
    path("playerresults/details", views.player_results, kwargs={'detailed': True}, name="player_results_detailed"),
    path("results/", views.results, name="results"),
]
