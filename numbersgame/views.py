import random
import os

from django.shortcuts import render, get_object_or_404
from django.db.models import Avg

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
                    Answer.objects.create(
                        game=game,
                        player=request.user.player,
                        answer=submit_answer_form.cleaned_data['answer'],
                        motivation=submit_answer_form.cleaned_data['motivation']
                    )
                    answer_submitted = True
            else:
                submit_answer_form = SubmitAnswerForm(game=game, player=request.user.player)
        else:
            player = None
    return render(request, os.path.join('numbers_game', 'submit_answer.html'), locals())


def results(request, session_slug_name, game_url_tag):
    session = get_object_or_404(Session, slug_name=session_slug_name)
    game = get_object_or_404(Game, url_tag=game_url_tag)

    answers = Answer.objects.filter(game=game).order_by('answer')
    if answers:
        average = answers.aggregate(Avg('answer'))['answer__avg']
        correctedAverage = average * 2 / 3
        bestAnswers = []
        smallestGap = 100
        for ans in answers:
            if abs(ans.answer - correctedAverage) < smallestGap:
                smallestGap = abs(ans.answer - correctedAverage)
                bestAnswers = [ans]
            elif abs(ans.answer - correctedAverage) == smallestGap:
                bestAnswers.append(ans)
        winners = str([ans.player.name for ans in bestAnswers])[1:-1]
        winningAnswers = str([ans.formattedAnswer() for ans in bestAnswers])[1:-1]
        shuffledAnswers = [a for a in answers]
        random.shuffle(shuffledAnswers)
        uniqueWinner = len(winners) == 1
    return render(request, os.path.join('numbers_game', 'results.html'), locals())
