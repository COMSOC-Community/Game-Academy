import random
import os

from django.shortcuts import render, get_object_or_404
from django.core import management
from django.http import Http404

from core.models import Session, Game, Player, Team
from core.views import is_session_admin

from .forms import SubmitAnswerForm
from .apps import AUCT_NAME
from .models import Answer


def index(request, session_slug_name, game_url_tag):
    session = get_object_or_404(Session, slug_name=session_slug_name)
    game = get_object_or_404(Game, session=session, url_tag=game_url_tag, game_type=AUCT_NAME)
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

    return render(request, os.path.join('auctiongame', 'index.html'), locals())


def submit_answer(request, session_slug_name, game_url_tag):
    session = get_object_or_404(Session, slug_name=session_slug_name)
    game = get_object_or_404(Game, session=session, url_tag=game_url_tag, game_type=AUCT_NAME)
    admin_user = is_session_admin(session, request.user)

    if not game.visible and not admin_user:
        raise Http404
    if not request.user.is_authenticated:
        raise Http404

    if request.user.is_authenticated:
        player = Player.objects.filter(session=session, user=request.user)
        if player.exists():
            player = player.first()

            try:
                current_answer = Answer.objects.get(game=game, player=player)
            except Answer.DoesNotExist:
                current_answer = Answer.objects.create(
                    game=game,
                    player=player,
                    auction_id=random.randint(1, 5),
                    bid=None,
                    utility=None,
                    motivation=''
                )
            if current_answer.bid is None:
                if request.method == "POST":
                    submit_answer_form = SubmitAnswerForm(request.POST, game=game, player=player)
                    if submit_answer_form.is_valid():
                        current_answer.bid = submit_answer_form.cleaned_data["bid"]
                        current_answer.utility = 10 + current_answer.auction_id - submit_answer_form.cleaned_data["bid"]
                        current_answer.motivation = submit_answer_form.cleaned_data["motivation"]
                        current_answer.save()
                        answer_submitted = True
                else:
                    submit_answer_form = SubmitAnswerForm(game=game, player=player)
        else:
            player = None
    return render(request, os.path.join('auctiongame', 'submit_answer.html'), locals())


def results(request, session_slug_name, game_url_tag):
    session = get_object_or_404(Session, slug_name=session_slug_name)
    game = get_object_or_404(Game, session=session, url_tag=game_url_tag, game_type=AUCT_NAME)
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
                    management.call_command("auct_generategraph", session=session.slug_name, game=game.url_tag)

    answers = Answer.objects.filter(game=game).order_by('-bid')
    if answers:
        winning_answers = answers.filter(winning=True)
        if winning_answers:
            winning_answers_formatted = sorted(list(set(answer.avg_score for answer in winning_answers)))
            if len(winning_answers_formatted) > 1:
                winning_answers_formatted = "{} and {}".format(winning_answers_formatted[0],
                                                               winning_answers_formatted[1])
            else:
                winning_answers_formatted = "{}".format(winning_answers_formatted[0])
            winners_formatted = sorted(list(answer.player.name for answer in winning_answers))
            if len(winners_formatted) > 1:
                winners_formatted[-1] = "and " + winners_formatted[-1]
            winners_formatted = ", ".join(winners_formatted)
    return render(request, os.path.join('centipedegame', 'results.html'), locals())