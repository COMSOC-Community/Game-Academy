from django.urls import path

from . import views
from .apps import URL_NAMESPACE

app_name = URL_NAMESPACE
urlpatterns = [
    path("", views.Index.as_view(), name="index"),
    path("answer/", views.SubmitAnswer.as_view(), name="submit_answer"),
    path("playerresults/", views.results, name="results"),
    path("global_results/", views.Results.as_view(), name="global_results"),
]
