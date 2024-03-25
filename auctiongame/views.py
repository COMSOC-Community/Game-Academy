import random
import os

from django.shortcuts import render, get_object_or_404
from django.http import Http404

from core.models import Session, Game
from core.views import base_context_initialiser, session_context_initialiser, \
    game_context_initialiser

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
    if context["answer"] and not context["answer"].bid:
        context["game_nav_display_answer"] = True

    return render(request, os.path.join("auctiongame", "index.html"), context)


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

    if submitting_player:
        # We initialise the answer to map the player to an auction.
        if not answer:
            answer = Answer.objects.create(
                game=game,
                player=submitting_player,
                auction_id=random.randint(1, 5),
                bid=None,
                utility=None,
                motivation="",
            )
            context["answer"] = answer

        if not answer.bid:
            if request.method == "POST":
                submit_answer_form = SubmitAnswerForm(
                    request.POST, game=game, player=submitting_player
                )
                if submit_answer_form.is_valid():
                    answer.bid = submit_answer_form.cleaned_data["bid"]
                    answer.utility = (
                        10
                        + answer.auction_id
                        - submit_answer_form.cleaned_data["bid"]
                    )
                    answer.motivation = submit_answer_form.cleaned_data[
                        "motivation"
                    ]
                    answer.save()
                    context["submitted_answer"] = answer
            else:
                submit_answer_form = SubmitAnswerForm(game=game, player=submitting_player)
            context["submit_answer_form"] = submit_answer_form
    return render(request, os.path.join("auctiongame", "submit_answer.html"), context)


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
        raise Http404("The results are not visible and the user is not an admin.")

    answers = Answer.objects.filter(game=game).order_by("auction_id", "-bid")
    context["answers"] = answers
    answers_per_auction = {
        str(auction_id): answers.filter(
            auction_id=auction_id, bid__isnull=False
        ).order_by("-bid")
        for auction_id in range(1, 6)
    }
    context["answers_per_auction"] = answers_per_auction
    formatted_winners = {str(auction_id): "" for auction_id in range(1, 6)}
    for auction_id, auction_answers in answers_per_auction.items():
        if auction_answers:
            winning_answers = auction_answers.filter(winning_auction=True)
            if winning_answers:
                winners_formatted = sorted(
                    list(answer.player.name for answer in winning_answers)
                )
                if len(winners_formatted) > 1:
                    winners_formatted[-1] = "and " + winners_formatted[-1]
                formatted_winners[auction_id] = ", ".join(winners_formatted)
    context["formatted_winners"] = formatted_winners
    global_winning_answers = answers.filter(winning_global=True)
    if global_winning_answers:
        global_winners_formatted = sorted(
            list(answer.player.name for answer in global_winning_answers)
        )
        if len(global_winners_formatted) > 1:
            global_winners_formatted[-1] = "and " + global_winners_formatted[-1]
        global_winners_formatted = ", ".join(global_winners_formatted)
        context["global_winners_formatted"] = global_winners_formatted
    return render(request, os.path.join("auctiongame", "results.html"), context)
