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

    try:
        current_player = Player.objects.get(session=session, user=request.user)
    except Player.DoesNotExist:
        current_player = None
    if current_player is not None:
        try:
            current_answer = Answer.objects.get(game=game, player=current_player)
        except Answer.DoesNotExist:
            current_answer = None

    answers = Answer.objects.filter(game=game).order_by('auction_id', '-bid')
    answers_per_auction = {str(auction_id): answers.filter(auction_id=auction_id).order_by('-bid')
                           for auction_id in range(1, 6)}
    formatted_winners = {str(auction_id): "" for auction_id in range(1, 6)}
    for auction_id, auction_answers in answers_per_auction.items():
        if auction_answers:
            winning_answers = auction_answers.filter(winning_auction=True)
            if winning_answers:
                winners_formatted = sorted(list(answer.player.name for answer in winning_answers))
                if len(winners_formatted) > 1:
                    winners_formatted[-1] = "and " + winners_formatted[-1]
                formatted_winners[auction_id] = ", ".join(winners_formatted)
    global_winning_answers = answers.filter(winning_global=True)
    if global_winning_answers:
        global_winners_formatted = sorted(list(answer.player.name for answer in global_winning_answers))
        if len(global_winners_formatted) > 1:
            global_winners_formatted[-1] = "and " + global_winners_formatted[-1]
        global_winners_formatted = ", ".join(global_winners_formatted)
    return render(request, os.path.join('auctiongame', 'results.html'), locals())
