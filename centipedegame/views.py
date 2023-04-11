import os

from django.shortcuts import render, get_object_or_404
from django.core import management
from django.http import Http404

from core.models import Session, Game, Player, Team
from core.views import is_session_admin

from .forms import SubmitAnswerForm
from .apps import CENTI_NAME
from .models import Answer


def index(request, session_slug_name, game_url_tag):
    session = get_object_or_404(Session, slug_name=session_slug_name)
    game = get_object_or_404(Game, session=session, url_tag=game_url_tag, game_type=CENTI_NAME)
    admin_user = is_session_admin(session, request.user)

    if not game.visible and not admin_user:
        raise Http404
    if not request.user.is_authenticated:
        raise Http404

    if request.user.is_authenticated:
        try:
            current_player = Player.objects.get(session=session, user=request.user)
        except Player.DoesNotExist:
            current_player = None
        if current_player is not None:
            try:
                current_answer = Answer.objects.get(game=game, player=current_player)
            except Answer.DoesNotExist:
                current_answer = None

    return render(request, os.path.join('centipedegame', 'index.html'), locals())


def submit_answer(request, session_slug_name, game_url_tag):
    session = get_object_or_404(Session, slug_name=session_slug_name)
    game = get_object_or_404(Game, session=session, url_tag=game_url_tag, game_type=CENTI_NAME)
    admin_user = is_session_admin(session, request.user)

    if not game.visible and not admin_user:
        raise Http404
    if not request.user.is_authenticated:
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
                                initial_state=submit_answer_form.cleaned_data['initial_state'],
                                automata=submit_answer_form.cleaned_data['automata'],
                                motivation=submit_answer_form.cleaned_data['motivation'],
                                name=submit_answer_form.cleaned_data['name'],
                            )
                            answer_submitted = True
                    else:
                        submit_answer_form = SubmitAnswerForm(game=game, team=team)
            else:
                team = None
        else:
            player = None
    return render(request, os.path.join('centipedegame', 'submit_answer.html'), locals())


def results(request, session_slug_name, game_url_tag):
    session = get_object_or_404(Session, slug_name=session_slug_name)
    game = get_object_or_404(Game, session=session, url_tag=game_url_tag, game_type=IPD_NAME)
    admin_user = is_session_admin(session, request.user)

    if not game.visible and not admin_user:
        raise Http404
    if not request.user.is_authenticated:
        raise Http404

    if admin_user:
        if request.method == "POST":
            if "form_type" in request.POST:
                if request.POST["form_type"] == "game_playable":
                    game.playable = not game.playable
                    game.save()
                elif request.POST["form_type"] == "results_visible":
                    game.results_visible = not game.results_visible
                    game.save()
                elif request.POST["form_type"] == "run_management":
                    management.call_command("ipd_computeresults", session=session.slug_name, game=game.url_tag)
                    management.call_command("ipd_generategraphdata", session=session.slug_name, game=game.url_tag)

    answers = Answer.objects.filter(game=game).order_by('-avg_score')
    return render(request, os.path.join('centipedegame', 'results.html'), locals())
