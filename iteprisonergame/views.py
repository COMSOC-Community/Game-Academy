import os

from django.http import Http404
from django.shortcuts import render, get_object_or_404

from core.models import Session, Game
from core.views import is_session_admin


def index(request, session_slug_name, game_url_tag):
    session = get_object_or_404(Session, slug_name=session_slug_name)
    game = get_object_or_404(Game, session=session, url_tag=game_url_tag)
    admin_user = is_session_admin(session, request.user)

    if not game.visible and not admin_user:
        raise Http404
    return render(request, os.path.join('iteprisonergame', 'index.html'), locals())


def submit_answer(request, session_slug_name, game_url_tag):
    session = get_object_or_404(Session, slug_name=session_slug_name)
    game = get_object_or_404(Game, session=session, url_tag=game_url_tag)
    admin_user = is_session_admin(session, request.user)

    if not game.visible and not admin_user:
        raise Http404
    return render(request, os.path.join('iteprisonergame', 'submit_answer.html'), locals())


def results(request, session_slug_name, game_url_tag):
    session = get_object_or_404(Session, slug_name=session_slug_name)
    game = get_object_or_404(Game, session=session, url_tag=game_url_tag)
    admin_user = is_session_admin(session, request.user)

    if not game.visible and not admin_user:
        raise Http404
    return render(request, os.path.join('iteprisonergame', 'results.html'), locals())
