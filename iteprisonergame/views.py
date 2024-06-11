import csv
import os

from django.http import HttpResponse
from django.shortcuts import render

from core.game_views import GameIndexView, GameSubmitAnswerView, GameResultsView
from .forms import SubmitAnswerForm
from .management.commands.ipd_generategraphdata import itepris_graph_data
from .models import Answer


class Index(GameIndexView):
    def get(self, request, session_url_tag, game_url_tag):
        return render(request, os.path.join("iteprisonergame", "index.html"), self.context)


class SubmitAnswer(GameSubmitAnswerView):
    def get(self, request, session_url_tag, game_url_tag):
        if self.context["submitting_player"] and not self.context["answer"]:
            self.context["submit_answer_form"] = SubmitAnswerForm(game=self.game, player=self.context["submitting_player"])
        return render(request, os.path.join("iteprisonergame", "submit_answer.html"), self.context)

    def post_validated_form(self, request):
        submit_answer_form = SubmitAnswerForm(
            request.POST, game=self.game, player=self.context["submitting_player"]
        )
        submit_answer_form.is_valid()
        return submit_answer_form

    def post_code_if_form_valid(self, request, form_object):
        new_answer = Answer.objects.create(
            game=self.game,
            player=self.context["submitting_player"],
            initial_state=form_object.cleaned_data["initial_state"],
            automata=form_object.cleaned_data["automata"],
            motivation=form_object.cleaned_data["motivation"],
            name=form_object.cleaned_data["name"],
        )
        new_answer.graph_json_data = itepris_graph_data(new_answer)
        new_answer.save()
        self.context["submitted_answer"] = new_answer

    def post_code_if_form_invalid(self, request, form_object):
        self.context["submit_answer_form"] = form_object

    def post_code_render(self, request):
        return render(request, os.path.join("iteprisonergame", "submit_answer.html"), self.context)


class Results(GameResultsView):

    def get(self, request, session_url_tag, game_url_tag):
        context = self.context
        all_answers = Answer.objects.filter(game=self.game)
        context["answers"] = all_answers.order_by("name")
        context["answers_sorted_score"] = all_answers.order_by("-avg_score")
        return render(request, os.path.join("iteprisonergame", "results.html"), context)


def export_answers(session, game):
    response = HttpResponse(content_type="text/csv")
    response["Content-Disposition"] = f'attachment; filename="{session.name}_{game.name}_answers.csv"'

    writer = csv.writer(response)
    writer.writerow(
        [
            "player_name",
            "is_team_player",
            "answer_name",
            "automata",
            "initial_state",
            "motivation",
            "avg_score",
            "winner"
        ]
    )
    for answer in Answer.objects.filter(game=game):
        writer.writerow([
            answer.player.name,
            answer.player.is_team_player,
            answer.name,
            answer.automata,
            answer.initial_state,
            answer.motivation,
            answer.avg_score,
            answer.winner
        ])
    return response
