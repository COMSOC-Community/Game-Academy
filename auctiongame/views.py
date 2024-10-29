import os
import random

from django.shortcuts import render

from core.game_views import GameResultsView, GameSubmitAnswerView, GameIndexView
from .forms import SubmitAnswerForm
from .models import Answer, Result
from .samplers import ALL_SAMPLERS


class Index(GameIndexView):
    def get(self, request, session_url_tag, game_url_tag):
        if self.context["answer"] and not self.context["answer"].bid:
            self.context["game_nav_display_answer"] = True
        return render(request, os.path.join("auctiongame", "index.html"), self.context)


class SubmitAnswer(GameSubmitAnswerView):
    def get(self, request, session_url_tag, game_url_tag):
        submitting_player = self.context["submitting_player"]
        if submitting_player:
            if not self.context["answer"]:
                auction_id = random.randint(1, self.game.auction_setting.number_auctions)
                answer = Answer.objects.create(
                    game=self.game,
                    player=submitting_player,
                    auction_id=auction_id,
                    valuation=ALL_SAMPLERS[self.game.auction_setting.valuation_sampler].sample(auction_id),
                    bid=None,
                    utility=None,
                    motivation="",
                )
                self.context["answer"] = answer

            if not self.context["answer"].bid:
                self.context["submit_answer_form"] = SubmitAnswerForm(
                    game=self.game, player=self.context["submitting_player"]
                )
        return render(
            request, os.path.join("auctiongame", "submit_answer.html"), self.context
        )

    def post_validated_form(self, request):
        submit_answer_form = SubmitAnswerForm(
            request.POST, game=self.game, player=self.context["submitting_player"]
        )
        if submit_answer_form.is_valid():
            return True, submit_answer_form
        else:
            return False, submit_answer_form

    def post_code_if_form_valid(self, request, form_object):
        answer = self.context["answer"]
        answer.bid = form_object.cleaned_data["bid"]
        answer.utility = 10 + answer.auction_id - form_object.cleaned_data["bid"]
        answer.motivation = form_object.cleaned_data["motivation"]
        answer.save()
        self.context["submitted_answer"] = answer

    def post_code_if_form_invalid(self, request, form_object):
        self.context["submit_answer_form"] = form_object

    def post_code_render(self, request):
        return render(
            request, os.path.join("auctiongame", "submit_answer.html"), self.context
        )


class Results(GameResultsView):
    def get(self, request, session_url_tag, game_url_tag):
        context = self.context

        answers = Answer.objects.filter(game=self.game).order_by("auction_id", "-bid")
        unique_auction_ids = answers.values_list('auction_id', flat=True).distinct()
        context["answers"] = answers
        answers_per_auction = {
            auction_id: Answer.objects.filter(auction_id=auction_id).order_by('-bid')
            for auction_id in unique_auction_ids
        }
        context["answers_per_auction"] = answers_per_auction
        formatted_winners = {str(auction_id): "" for auction_id in range(1, 6)}
        for auction_id, auction_answers in answers_per_auction.items():
            if auction_answers:
                winning_answers = auction_answers.filter(winning_auction=True)
                if winning_answers:
                    winners_formatted = sorted(
                        list(answer.player.name for answer in winning_answers)
                    )
                    if len(winners_formatted) > 1:
                        winners_formatted[-1] = "and " + winners_formatted[-1]
                    formatted_winners[auction_id] = ", ".join(winners_formatted)
        all_results = Result.objects.filter(game=self.game)
        context["result_per_auction"] = {
            auction_id: all_results.filter(auction_id=auction_id).first() for auction_id in unique_auction_ids
        }
        context["formatted_winners"] = formatted_winners
        global_winning_answers = answers.filter(winning_global=True)
        if global_winning_answers:
            global_winners_formatted = sorted(
                list(answer.player.name for answer in global_winning_answers)
            )
            if len(global_winners_formatted) > 1:
                global_winners_formatted[-1] = "and " + global_winners_formatted[-1]
            global_winners_formatted = ", ".join(global_winners_formatted)
            context["global_winners_formatted"] = global_winners_formatted
        return render(request, os.path.join("auctiongame", "results.html"), context)
