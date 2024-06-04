from django.urls import path

from . import views

from .apps import URL_NAMESPACE

app_name = URL_NAMESPACE
urlpatterns = [
    path("", views.index, name="index"),
    path("answer/", views.submit_answer, name="submit_answer"),
    path("global_results/", views.results, name="global_results"),
]
