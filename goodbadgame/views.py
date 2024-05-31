import os
import random

from django.http import Http404
from django.shortcuts import render, get_object_or_404, redirect
from django.core import management
from django.urls import reverse

from slugify import slugify

from core.models import Game, Session
from core.views import base_context_initialiser, session_context_initialiser, \
    game_context_initialiser
from .apps import NAME
from .forms import *
from .models import Answer, Alternative


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

    if not submitting_player.questions.exists():
        pks = list(game.goodbad_setting.questions.values_list('pk', flat=True))
        pks = random.sample(pks, min(len(pks), game.goodbad_setting.questions.num_displayed_questions))
        submitting_player.questions.add(*game.goodbad_setting.questions.filter(pk__in=pks))
        submitting_player.save()

    if submitting_player and not answer:
        questions = list(submitting_player.questions.all())
        random.shuffle(questions)
        if request.method == "POST":
            for question in questions:
                if question.slug + "_selector" in request.POST:
                    Answer.objects.create(
                        question=question,
                        player=submitting_player,
                        answer=question.alternatives.get(
                            id=request.POST.get(question.slug + "_selector")),
                        is_correct=Alternative.objects.get(id=request.POST.get(
                            question.slug + "_selector")) == question.correct_alt
                    )
            management.call_command("goodbad_updategraphdata", session=session.url_tag, game=game.url_tag, player=submitting_player.name)

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


def submit_answer(request, session_slug, player_slug):
    session = get_object_or_404(Session, slug=session_slug)
    player = get_object_or_404(Player, slug=player_slug, session=session)
    already_played = False
    if not player.questions.exists():
        pks = list(session.questions.values_list('pk', flat=True))
        pks = random.sample(pks, min(session.questions.count(), session.num_displayed_questions))
        player.questions.add(*session.questions.filter(pk__in=pks))
        player.save()
    if Answer.objects.filter(player=player).exists():
        already_played = True
    else:
        questions = list(player.questions.all())
        shuffle(questions)
        if request.method == "POST":
            for question in questions:
                if question.slug + "_selector" in request.POST:
                    Answer.objects.create(
                        question=question,
                        player=player,
                        answer=question.alternatives.get(id=request.POST.get(question.slug + "_selector")),
                        is_correct=Alternative.objects.get(id=request.POST.get(question.slug + "_selector")) == question.correct_alt
                    )
            management.call_command("updatejsgraphdata", session=session.slug, player=player.name)
            return redirect(reverse('goodbad:goodbad_result', kwargs={'session_slug': session.slug,
                                                                      'player_slug': player.slug}))
    return render(request, os.path.join('goodbad', 'goodbad_play.html'), locals())


def player_results(request, session_slug, player_slug, detailed=False):
    session = get_object_or_404(Session, slug=session_slug)
    player = get_object_or_404(Player, slug=player_slug, session=session)
    global_results = False
    detailed = detailed

    questions_answers = []
    for question in player.questions.all():
        answer = question.answers.filter(player=player)
        if answer.exists():
            answer = answer.first()
        else:
            answer = None

        if detailed:
            try:
                graph_js_data = JSGraphData.objects.get(session=session, question=question)
            except JSGraphData.DoesNotExist:
                graph_js_data = None
            questions_answers.append((question, answer, question.crowd_count(session), graph_js_data))
        else:
            questions_answers.append((question, answer, question.crowd_count(session)))

    player_global_count = player.questions_count()
    session_global_count = session.questions_count()
    if sum(session_global_count) > 0:
        crowd_accuracy = int(10000 * session_global_count[1] / sum(session_global_count)) / 100
    else:
        crowd_accuracy = 0
    if sum(player_global_count) > 0:
        player_accuracy = int(10000 * player_global_count[1] / sum(player_global_count)) / 100
    else:
        player_accuracy = 0

    return render(request, os.path.join('goodbad', 'goodbad_result.html'), locals())


def results(request, session_slug):
    if not request.user.is_authenticated:
        raise Http404
    session = get_object_or_404(Session, slug=session_slug)
    global_results = True
    detailed = True

    questions_answers = []
    for question in session.questions.all():
        try:
            graph_js_data = JSGraphData.objects.get(session=session, question=question)
        except JSGraphData.DoesNotExist:
            graph_js_data = None
        questions_answers.append((question, None, question.crowd_count(session), graph_js_data))

    session_global_count = session.questions_count()
    if sum(session_global_count) > 0:
        crowd_accuracy = int(10000 * session_global_count[1] / sum(session_global_count)) / 100
    else:
        crowd_accuracy = 0

    return render(request, os.path.join('goodbad', 'goodbad_result.html'), locals())
