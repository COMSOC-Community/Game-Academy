import os

from django.shortcuts import render, get_object_or_404
from django.http import Http404

from core.models import Session, Game
from core.views import (
    base_context_initialiser,
    session_context_initialiser,
    game_context_initialiser,
)

from .forms import SubmitAnswerForm
from .apps import NAME
from .management.commands.ipd_generategraphdata import itepris_graph_data
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

    return render(request, os.path.join("iteprisonergame", "index.html"), context)


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
        submit_answer_form = SubmitAnswerForm(game=game, player=submitting_player)
        if request.method == "POST":
            submit_answer_form = SubmitAnswerForm(
                request.POST, game=game, player=submitting_player
            )
            if submit_answer_form.is_valid():
                new_answer = Answer.objects.create(
                    game=game,
                    player=submitting_player,
                    initial_state=submit_answer_form.cleaned_data["initial_state"],
                    automata=submit_answer_form.cleaned_data["automata"],
                    motivation=submit_answer_form.cleaned_data["motivation"],
                    name=submit_answer_form.cleaned_data["name"],
                )
                new_answer.graph_json_data = itepris_graph_data(new_answer)
                new_answer.save()
                context["submitted_answer"] = new_answer
        context["submit_answer_form"] = submit_answer_form
    return render(
        request, os.path.join("iteprisonergame", "submit_answer.html"), context
    )


def results(request, session_url_tag, game_url_tag):
    session = get_object_or_404(Session, url_tag=session_url_tag)
    game = get_object_or_404(
        Game, session=session, url_tag=game_url_tag, game_type=NAME
    )

    context = base_context_initialiser(request)
    session_context_initialiser(request, session, context)
    game_context_initialiser(request, session, game, Answer, context)
    context["game_nav_display_result"] = False

    all_answers = Answer.objects.filter(game=game)
    context["answers"] = all_answers.order_by("name")
    context["answers_sorted_score"] = all_answers.order_by("-avg_score")
    return render(request, os.path.join("iteprisonergame", "results.html"), context)
