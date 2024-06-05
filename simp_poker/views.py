import os

from django.shortcuts import render

from core.game_views import GameIndexView, GameSubmitAnswerView, GameResultsView
from .forms import SubmitAnswerForm
from .management.commands.simppoker_computeresults import get_score_against_opt
from .models import Answer


class Index(GameIndexView):
    def get(self, request, session_url_tag, game_url_tag):
        return render(request, os.path.join("simp_poker", "index.html"), self.context)


class SubmitAnswer(GameSubmitAnswerView):
    def get(self, request, session_url_tag, game_url_tag):
        if self.context["submitting_player"] and not self.context["answer"]:
            self.context["submit_answer_form"] = SubmitAnswerForm(game=self.game, player=self.context["submitting_player"])
        return render(request, os.path.join("simp_poker", "submit_answer.html"), self.context)

    def post_validated_form(self, request):
        submit_answer_form = SubmitAnswerForm(
            request.POST, game=self.game, player=self.context["submitting_player"]
        )
        submit_answer_form.is_valid()
        return submit_answer_form

    def post_code_if_form_valid(self, request, form_object):
        answer = Answer.objects.create(
            game=self.game,
            player=self.context["submitting_player"],
            prob_p1_king=form_object.cleaned_data["prob_p1_king"],
            prob_p1_queen=form_object.cleaned_data["prob_p1_queen"],
            prob_p1_jack=form_object.cleaned_data["prob_p1_jack"],
            prob_p2_king=form_object.cleaned_data["prob_p2_king"],
            prob_p2_queen=form_object.cleaned_data["prob_p2_queen"],
            prob_p2_jack=form_object.cleaned_data["prob_p2_jack"],
            motivation=form_object.cleaned_data["motivation"],
        )
        try:
            answer.score_against_optimum = get_score_against_opt(answer)
            answer.save()
            self.context["submitted_answer"] = answer
        except Exception as e:
            answer.delete()
            self.context["submission_error"] = e.__repr__()
            self.context["submitted_answer"] = False

    def post_code_if_form_invalid(self, request, form_object):
        self.context["submit_answer_form"] = form_object

    def post_code_render(self, request):
        return render(request, os.path.join("simp_poker", "submit_answer.html"), self.context)


class Results(GameResultsView):

    def get(self, request, session_url_tag, game_url_tag):
        game = self.game
        context = self.context
        answers = Answer.objects.filter(game=game)
        context["answers_sorted_round_robin"] = answers.order_by('-round_robin_score')
        context["answers_sorted_round_robin_with_opt"] = answers.order_by('-round_robin_with_opt_score')
        context["answers_sorted_against_opt"] = answers.order_by('-score_against_optimum')

        round_robin_winners = answers.filter(round_robin_position=1)
        if round_robin_winners:
            if len(round_robin_winners) == 1:
                context["formatted_round_robin_winners"] = round_robin_winners.first().player.display_name()
            else:
                winners = [f"<em>{a.player.display_name()}</em>" for a in round_robin_winners]
                context["formatted_round_robin_winners"] = ', '.join(winners[:-1]) + ' and ' + winners[-1]
                context["several_winners_round_robin"] = True

        winners_agains_opt = answers.filter(winner_against_optimum=True)
        if winners_agains_opt:
            if len(winners_agains_opt) == 1:
                context["formatted_winners_against_opt"] = winners_agains_opt.first().player.display_name()
            else:
                winners = [f"<em>{a.player.display_name()}</em>" for a in winners_agains_opt]
                context["formatted_winners_against_opt"] = ', '.join(winners[:-1]) + ' and ' + winners[-1]
                context["several_winners_against_opt"] = True

        context["optimal_strategy"] = Answer(
            prob_p1_king=1,
            prob_p1_queen=1,
            prob_p1_jack=1/3,
            prob_p2_king=1,
            prob_p2_queen=1/3,
            prob_p2_jack=0
        )

        return render(request, os.path.join("simp_poker", "global_results.html"), context)
