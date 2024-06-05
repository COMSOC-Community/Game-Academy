import os
import random

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
        submit_answer_form.is_valid()
        return submit_answer_form

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
                winning_answers_formatted = sorted(
                    list(set(answer.answer for answer in winning_answers))
                )
                if len(winning_answers_formatted) > 1:
                    winning_answers_formatted = "{} and {}".format(
                        winning_answers_formatted[0], winning_answers_formatted[1]
                    )
                else:
                    winning_answers_formatted = "{}".format(winning_answers_formatted[0])
                context["winning_answers_formatted"] = winning_answers_formatted
                winners_formatted = sorted(
                    list(answer.player.name for answer in winning_answers)
                )
                if len(winners_formatted) > 1:
                    winners_formatted[-1] = "and " + winners_formatted[-1]
                winners_formatted = ", ".join(winners_formatted)
                context["winners_formatted"] = winners_formatted
        return render(request, os.path.join("numbers_game", "results.html"), context)
