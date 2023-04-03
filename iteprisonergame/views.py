import os

from django.http import Http404
from django.shortcuts import render, get_object_or_404

from core.models import Session, Game, Player, Team
from core.views import is_session_admin

from .forms import SubmitAnswerForm
from .apps import IP_NAME
from .models import Answer


def index(request, session_slug_name, game_url_tag):
    session = get_object_or_404(Session, slug_name=session_slug_name)
    game = get_object_or_404(Game, session=session, url_tag=game_url_tag, game_type=IP_NAME)
    admin_user = is_session_admin(session, request.user)

    if not game.visible and not admin_user:
        raise Http404

    if request.user.is_authenticated:
        try:
            current_player = Player.objects.get(session=session, user=request.user)
        except Player.DoesNotExist:
            current_player = None
        if current_player is not None:
            try:
                current_team = current_player.teams.get(game=game)
            except Team.DoesNotExist:
                current_team = None
            if current_team is not None:
                try:
                    current_answer = Answer.objects.get(game=game, team=current_team)
                except Answer.DoesNotExist:
                    current_answer = None

    return render(request, os.path.join('iteprisonergame', 'index.html'), locals())


def submit_answer(request, session_slug_name, game_url_tag):
    session = get_object_or_404(Session, slug_name=session_slug_name)
    game = get_object_or_404(Game, session=session, url_tag=game_url_tag, game_type=IP_NAME)
    admin_user = is_session_admin(session, request.user)

    if not game.visible and not admin_user:
        raise Http404

    if request.user.is_authenticated:
        player = Player.objects.filter(session=session, user=request.user)
        if player.exists():
            player = player.first()

            team = player.teams.filter(game=game)
            if team.exists():
                team = team.first()
                try:
                    current_answer = Answer.objects.get(game=game, team=team)
                except Answer.DoesNotExist:
                    current_answer = None
                if current_answer is None:
                    if request.method == "POST":
                        submit_answer_form = SubmitAnswerForm(request.POST, game=game, team=team)
                        if submit_answer_form.is_valid():
                            new_answer = Answer.objects.create(
                                game=game,
                                team=team,
                                automata=submit_answer_form.cleaned_data['automata'],
                                motivation=submit_answer_form.cleaned_data['motivation'],
                                name=submit_answer_form.cleaned_data['name'],
                                score=0,
                                winner=False
                            )
                            answer_submitted = True
                    else:
                        submit_answer_form = SubmitAnswerForm(game=game, team=team)
            else:
                team = None
        else:
            player = None
    return render(request, os.path.join('iteprisonergame', 'submit_answer.html'), locals())


def results(request, session_slug_name, game_url_tag):
    session = get_object_or_404(Session, slug_name=session_slug_name)
    game = get_object_or_404(Game, session=session, url_tag=game_url_tag, game_type=IP_NAME)
    admin_user = is_session_admin(session, request.user)

    if not game.visible and not admin_user:
        raise Http404
    return render(request, os.path.join('iteprisonergame', 'results.html'), locals())
