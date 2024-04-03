import os

from django.http import Http404
from django.shortcuts import render, get_object_or_404

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

    return render(request, os.path.join("simp_poker", "index.html"), context)


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
                context["submitted_answer"] = Answer.objects.create(
                    game=game,
                    player=submitting_player,
                    prob_p1_king=submit_answer_form.cleaned_data["prob_p1_king"],
                    prob_p1_queen=submit_answer_form.cleaned_data["prob_p1_queen"],
                    prob_p1_jack=submit_answer_form.cleaned_data["prob_p1_jack"],
                    prob_p2_king=submit_answer_form.cleaned_data["prob_p2_king"],
                    prob_p2_queen=submit_answer_form.cleaned_data["prob_p2_queen"],
                    prob_p2_jack=submit_answer_form.cleaned_data["prob_p2_jack"],
                    motivation=submit_answer_form.cleaned_data["motivation"],
                )
        else:
            submit_answer_form = SubmitAnswerForm(game=game, player=submitting_player)
        context["submit_answer_form"] = submit_answer_form
    return render(request, os.path.join("simp_poker", "submit_answer.html"), context)


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

    answers = Answer.objects.filter(game=game)
    context["answers_sorted_round_robin"] = answers.order_by('-round_robin_score')
    context["answers_sorted_round_robin_with_opt"] = answers.order_by('-round_robin_with_opt_score')
    context["answers_sorted_against_opt"] = answers.order_by('-score_against_optimum')

    round_robin_winners = answers.filter(round_robin_position=1)
    if round_robin_winners:
        if len(round_robin_winners) == 1:
            context["formatted_round_robin_winners"] = round_robin_winners.first().player.display_name()
        else:
            winners = [f"'<em>{a.player.display_name()}</em>'" for a in round_robin_winners]
            context["formatted_round_robin_winners"] = ','.join(winners[:-1]) + ' and ' + winners[-1]

    winners_agains_opt = answers.filter(winner_against_optimum=True)
    if winners_agains_opt:
        if len(winners_agains_opt) == 1:
            context["formatted_winners_against_opt"] = winners_agains_opt.first().player.display_name()
        else:
            winners = [f"'<em>{a.player.display_name()}</em>'" for a in winners_agains_opt]
            context["formatted_winners_against_opt"] = ','.join(winners[:-1]) + ' and ' + winners[-1]

    return render(request, os.path.join("simp_poker", "results.html"), context)
