import os
import random

from django.http import Http404
from django.shortcuts import render, get_object_or_404, redirect
from django.core import management
from django.urls import reverse

from slugify import slugify

from .forms import *


def goodbad_index(request, session_slug):
    session = get_object_or_404(Session, slug=session_slug)
    if request.method == "POST":
        form = PlayerForm(request.POST, session=session)
        if form.is_valid():
            name = form.cleaned_data['name']
            slug = slugify(name)
            slug_index = 1
            while Player.objects.filter(slug=slug + "_" + str(slug_index), session=session).exists():
                slug_index += 1
            slug += "_" + str(slug_index)
            player = Player.objects.create(
                name=name,
                slug=slug,
                session=session,
            )
            return redirect(reverse('goodbad:goodbad_play', kwargs={'session_slug': session.slug,
                                                                    'player_slug': player.slug}))
    else:
        form = PlayerForm(session=session)
    return render(request, os.path.join('goodbad', 'index.html'), locals())


def goodbad_play(request, session_slug, player_slug):
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


def goodbad_result(request, session_slug, player_slug, detailed=False):
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


def goodbad_detailed_result_all(request, session_slug):
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
