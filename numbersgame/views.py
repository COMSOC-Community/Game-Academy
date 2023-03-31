import random
import os

from django.shortcuts import render, get_object_or_404
from django.db.models import Avg, F, Func
from django.core import management

from core.models import Session, Game, Player
from core.views import is_session_admin

from .forms import SubmitAnswerForm
from .models import Answer


def index(request, session_slug_name, game_url_tag):
    session = get_object_or_404(Session, slug_name=session_slug_name)
    game = get_object_or_404(Game, url_tag=game_url_tag)
    admin_user = is_session_admin(session, request.user)

    return render(request, os.path.join('numbers_game', 'index.html'), locals())


def submit_answer(request, session_slug_name, game_url_tag):
    session = get_object_or_404(Session, slug_name=session_slug_name)
    game = get_object_or_404(Game, url_tag=game_url_tag)
    admin_user = is_session_admin(session, request.user)

    if request.user.is_authenticated:
        player = Player.objects.filter(session=session, user=request.user)
        if player.exists():
            player = player.first()
            if request.method == "POST":
                submit_answer_form = SubmitAnswerForm(request.POST, game=game, player=request.user.player)
                if submit_answer_form.is_valid():
                    new_answer = Answer.objects.create(
                        game=game,
                        player=request.user.player,
                        answer=submit_answer_form.cleaned_data['answer'],
                        motivation=submit_answer_form.cleaned_data['motivation']
                    )
                    try:
                        management.call_command("ng_updateresults", session=session.slug_name, game=game.url_tag)
                        answer_submitted = True
                    except Exception as e:
                        submission_error = repr(e)
                        new_answer.delete()
            else:
                submit_answer_form = SubmitAnswerForm(game=game, player=request.user.player)
        else:
            player = None
    return render(request, os.path.join('numbers_game', 'submit_answer.html'), locals())


def results(request, session_slug_name, game_url_tag):
    session = get_object_or_404(Session, slug_name=session_slug_name)
    game = get_object_or_404(Game, url_tag=game_url_tag)
    admin_user = is_session_admin(session, request.user)

    answers = Answer.objects.filter(game=game, answer__isnull=False).order_by('answer')
    if answers:
        shuffled_answers = list(answers)
        random.shuffle(shuffled_answers)
        winning_answers = answers.filter(winner=True)
        if winning_answers:
            winning_answers_formatted = sorted(list(set(answer.answer for answer in winning_answers)))
            if len(winning_answers_formatted) > 1:
                winning_answers_formatted = "{} and {}".format(winning_answers_formatted[0], winning_answers_formatted[1])
            else:
                winning_answers_formatted = "{}".format(winning_answers_formatted[0])
            winners_formatted = sorted(list(answer.player.name for answer in winning_answers))
            if len(winners_formatted) > 1:
                winners_formatted[-1] = "and " + winners_formatted[-1]
            winners_formatted = ", ".join(winners_formatted)
    return render(request, os.path.join('numbers_game', 'results.html'), locals())
