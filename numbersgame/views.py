import random
import os

from django.http import Http404
from django.shortcuts import render, get_object_or_404
from django.core import management

from core.models import Session, Game, Player
from core.views import is_session_admin

from .forms import SubmitAnswerForm
from .apps import NAME
from .models import Answer


def index(request, session_url_tag, game_url_tag):
    session = get_object_or_404(Session, url_tag=session_url_tag)
    game = get_object_or_404(
        Game, session=session, url_tag=game_url_tag, game_type=NAME
    )
    context = {
        "session": session,
        "game": game,
        "admin_user": is_session_admin(session, request.user),
    }
    try:
        player = Player.objects.get(session=session, user=request.user)
        context["player"] = player
        answer = Answer.objects.get(game=game, player=player)
        context["answer"] = answer
    except (Player.DoesNotExist, Answer.DoesNotExist):
        pass

    return render(request, os.path.join("numbers_game", "index.html"), context)


def submit_answer(request, session_url_tag, game_url_tag):
    session = get_object_or_404(Session, url_tag=session_url_tag)
    game = get_object_or_404(
        Game, session=session, url_tag=game_url_tag, game_type=NAME
    )
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
                current_answer = Answer.objects.get(
                    game=game, player=player
                )
            except Answer.DoesNotExist:
                current_answer = None
            if current_answer is None:
                if request.method == "POST":
                    submit_answer_form = SubmitAnswerForm(
                        request.POST, game=game, player=player
                    )
                    if submit_answer_form.is_valid():
                        new_answer = Answer.objects.create(
                            game=game,
                            player=player,
                            answer=submit_answer_form.cleaned_data["answer"],
                            motivation=submit_answer_form.cleaned_data["motivation"],
                        )
                        try:
                            management.call_command(
                                "ng_updateresults",
                                session=session.url_tag,
                                game=game.url_tag,
                            )
                            answer_submitted = True
                        except Exception as e:
                            submission_error = repr(e)
                            new_answer.delete()
                else:
                    submit_answer_form = SubmitAnswerForm(
                        game=game, player=player
                    )
        else:
            player = None
    return render(request, os.path.join("numbers_game", "submit_answer.html"), locals())


def results(request, session_url_tag, game_url_tag):
    session = get_object_or_404(Session, url_tag=session_url_tag)
    game = get_object_or_404(
        Game, session=session, url_tag=game_url_tag, game_type=NAME
    )
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
                    management.call_command(
                        "ng_updateresults", session=session.url_tag, game=game.url_tag
                    )

    answers = Answer.objects.filter(game=game, answer__isnull=False).order_by("answer")
    if answers:
        shuffled_answers = list(answers)
        random.shuffle(shuffled_answers)
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
            winners_formatted = sorted(
                list(answer.player.name for answer in winning_answers)
            )
            if len(winners_formatted) > 1:
                winners_formatted[-1] = "and " + winners_formatted[-1]
            winners_formatted = ", ".join(winners_formatted)
    return render(request, os.path.join("numbers_game", "results.html"), locals())
