import os
import random

from django.http import Http404
from django.shortcuts import render, get_object_or_404
from django.core import management

from core.models import Game, Session
from core.views import base_context_initialiser, session_context_initialiser, \
    game_context_initialiser
from .apps import NAME
from .models import Answer, Alternative, QuestionAnswer, QuestionResult, Result


def index(request, session_url_tag, game_url_tag):
    session = get_object_or_404(Session, url_tag=session_url_tag)
    game = get_object_or_404(
        Game, session=session, url_tag=game_url_tag, game_type=NAME
    )

    context = base_context_initialiser(request)
    session_context_initialiser(request, session, context)
    game_context_initialiser(request, session, game, Answer, context)
    context["game_nav_display_home"] = False
    if context["answer"] and not context["answer"].score:
        context["game_nav_display_answer"] = True

    return render(request, os.path.join("goodbad", "index.html"), context)


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
        if not answer:
            answer = Answer.objects.create(game=game, player=submitting_player)
            pks = list(game.goodbad_setting.questions.values_list('pk', flat=True))
            pks = random.sample(pks, min(len(pks), game.goodbad_setting.num_displayed_questions))
            answer.questions.add(*game.goodbad_setting.questions.filter(pk__in=pks))
            answer.save()
            context["answer"] = answer

        if not answer.score:
            questions = list(answer.questions.all())
            random.shuffle(questions)
            if request.method == "POST":
                for question in questions:
                    if question.slug + "_selector" in request.POST:
                        QuestionAnswer.objects.create(
                            answer=answer,
                            question=question,
                            selected_alt=question.alternatives.get(
                                id=request.POST.get(question.slug + "_selector")),
                            is_correct=Alternative.objects.get(id=request.POST.get(
                                question.slug + "_selector")) == question.correct_alt
                        )
                management.call_command("goodbad_updateresults", session=session.url_tag, game=game.url_tag, player=submitting_player.name)
                context["submitted_answer"] = True

    return render(request, os.path.join("goodbad", "submit_answer.html"), context)


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

    answer = context["answer"]
    game_result = Result.objects.filter(game=game).first()

    if game_result:
        context["game_result"] = game_result
        if answer:
            questions_answer_result = []
            for question in answer.questions.all():
                question_answer = answer.question_answers.filter(question=question).first()
                question_result = question.results.filter(result=game_result).first()
                questions_answer_result.append((question, question_answer, question_result))
            context["questions_answer_result"] = questions_answer_result

    return render(request, os.path.join('goodbad', 'results.html'), context)


def global_results(request, session_url_tag, game_url_tag):
    session = get_object_or_404(Session, url_tag=session_url_tag)
    game = get_object_or_404(
        Game, session=session, url_tag=game_url_tag, game_type=NAME
    )

    context = base_context_initialiser(request)
    session_context_initialiser(request, session, context)
    game_context_initialiser(request, session, game, Answer, context)
    context["game_nav_display_result"] = False
    game_result = Result.objects.filter(game=game).first()

    if game_result:
        context["global_results"] = True
        context["game_result"] = game_result

        questions_answer_result = []
        for question in game.goodbad_setting.questions.all():
            question_result = question.results.filter(result=game_result).first()
            questions_answer_result.append((question, None, question_result))
        context["questions_answer_result"] = questions_answer_result

    context["global_results"] = True
    return render(request, os.path.join('goodbad', 'results.html'), context)
