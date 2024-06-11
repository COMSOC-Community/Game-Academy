import csv
import os
import random

from django.http import HttpResponse
from django.shortcuts import render

from core.game_views import GameIndexView, GameSubmitAnswerView, GameResultsView
from .forms import SubmitAnswerForm
from .models import Answer


class Index(GameIndexView):
    def get(self, request, session_url_tag, game_url_tag):
        return render(request, os.path.join("numbers_game", "index.html"), self.context)


class SubmitAnswer(GameSubmitAnswerView):
    def get(self, request, session_url_tag, game_url_tag):
        if self.context["submitting_player"] and not self.context["answer"]:
            self.context["submit_answer_form"] = SubmitAnswerForm(game=self.game, player=self.context["submitting_player"])
        return render(request, os.path.join("numbers_game", "submit_answer.html"), self.context)

    def post_validated_form(self, request):
        submit_answer_form = SubmitAnswerForm(
            request.POST, game=self.game, player=self.context["submitting_player"]
        )
        if submit_answer_form.is_valid():
            return True, submit_answer_form
        else:
            return False, submit_answer_form

    def post_code_if_form_valid(self, request, form_object):
        self.context["submitted_answer"] = Answer.objects.create(
            game=self.game,
            player=self.context["submitting_player"],
            answer=form_object.cleaned_data["answer"],
            motivation=form_object.cleaned_data["motivation"],
        )

    def post_code_if_form_invalid(self, request, form_object):
        self.context["submit_answer_form"] = form_object

    def post_code_render(self, request):
        return render(request, os.path.join("numbers_game", "submit_answer.html"), self.context)


class Results(GameResultsView):

    def get(self, request, session_url_tag, game_url_tag):
        game = self.game
        context = self.context
        answers = Answer.objects.filter(game=game, answer__isnull=False).order_by("answer")
        if answers:
            context["answers"] = answers
            shuffled_answers = list(answers)
            random.shuffle(shuffled_answers)
            context["shuffled_answers"] = shuffled_answers
            winning_answers = answers.filter(winner=True)
            if winning_answers:
                context["winning_answers"] = winning_answers
                context["winning_numbers"] = winning_answers.order_by('answer').values_list('answer', flat=True).distinct()
        return render(request, os.path.join("numbers_game", "results.html"), context)


def export_answers(session, game):
    response = HttpResponse(content_type="text/csv")
    response["Content-Disposition"] = f'attachment; filename="{session.name}_{game.name}_answers.csv"'

    writer = csv.writer(response)
    writer.writerow(
        [
            "player_name",
            "is_team_player",
            "answer",
            "motivation",
            "gap",
            "winner"
        ]
    )
    for answer in Answer.objects.filter(game=game):
        writer.writerow([
            answer.player.name,
            answer.player.is_team_player,
            answer.answer,
            answer.motivation,
            answer.gap,
            answer.winner
        ])
    return response
