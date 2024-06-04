import random
import os

from django.http import Http404
from django.shortcuts import render, get_object_or_404
from django.core import management

from core.models import Session, Game
from core.views import (
    base_context_initialiser,
    session_context_initialiser,
    game_context_initialiser,
)

from .forms import SubmitAnswerForm
from .apps import NAME
from .models import Answer


def index(request, session_url_tag, game_url_tag):
    session = get_object_or_404(Session, url_tag=session_url_tag)
    game = get_object_or_404(
        Game, session=session, url_tag=game_url_tag, game_type=NAME
    )

    context = base_context_initialiser(request)
    session_context_initialiser(request, session, context)
    game_context_initialiser(request, session, game, Answer, context)
    context["game_nav_display_home"] = False

    return render(request, os.path.join("numbers_game", "index.html"), context)


def submit_answer(request, session_url_tag, game_url_tag):
    session = get_object_or_404(Session, url_tag=session_url_tag)
    game = get_object_or_404(
        Game, session=session, url_tag=game_url_tag, game_type=NAME
    )

    context = base_context_initialiser(request)
    session_context_initialiser(request, session, context)
    game_context_initialiser(request, session, game, Answer, context)
    context["game_nav_display_answer"] = False

    if not game.playable and not context["user_is_session_admin"]:
        raise Http404("The game is not playable and the user is not an admin.")

    submitting_player = context["submitting_player"]
    answer = context["answer"]

    if submitting_player and not answer:
        if request.method == "POST":
            submit_answer_form = SubmitAnswerForm(
                request.POST, game=game, player=submitting_player
            )
            if submit_answer_form.is_valid():
                submitted_answer = Answer.objects.create(
                    game=game,
                    player=submitting_player,
                    answer=submit_answer_form.cleaned_data["answer"],
                    motivation=submit_answer_form.cleaned_data["motivation"],
                )
                try:
                    management.call_command(
                        "ng_results",
                        session=session.url_tag,
                        game=game.url_tag,
                    )
                    context["submitted_answer"] = submitted_answer
                except Exception as e:
                    submitted_answer.delete()
                    context["submission_error"] = repr(e)
        else:
            submit_answer_form = SubmitAnswerForm(game=game, player=submitting_player)
        context["submit_answer_form"] = submit_answer_form
    return render(request, os.path.join("numbers_game", "submit_answer.html"), context)


def results(request, session_url_tag, game_url_tag):
    session = get_object_or_404(Session, url_tag=session_url_tag)
    game = get_object_or_404(
        Game, session=session, url_tag=game_url_tag, game_type=NAME
    )

    context = base_context_initialiser(request)
    session_context_initialiser(request, session, context)
    game_context_initialiser(request, session, game, Answer, context)
    context["game_nav_display_result"] = False

    if not game.results_visible and not context["user_is_session_admin"]:
        raise Http404("The global_results are not visible and the user is not an admin.")

    answers = Answer.objects.filter(game=game, answer__isnull=False).order_by("answer")
    if answers:
        context["answers"] = answers
        shuffled_answers = list(answers)
        random.shuffle(shuffled_answers)
        context["shuffled_answers"] = shuffled_answers
        winning_answers = answers.filter(winner=True)
        if winning_answers:
            winning_answers_formatted = sorted(
                list(set(answer.answer for answer in winning_answers))
            )
            if len(winning_answers_formatted) > 1:
                winning_answers_formatted = "{} and {}".format(
                    winning_answers_formatted[0], winning_answers_formatted[1]
                )
            else:
                winning_answers_formatted = "{}".format(winning_answers_formatted[0])
            context["winning_answers_formatted"] = winning_answers_formatted
            winners_formatted = sorted(
                list(answer.player.name for answer in winning_answers)
            )
            if len(winners_formatted) > 1:
                winners_formatted[-1] = "and " + winners_formatted[-1]
            winners_formatted = ", ".join(winners_formatted)
            context["winners_formatted"] = winners_formatted
    return render(request, os.path.join("numbers_game", "global_results.html"), context)
