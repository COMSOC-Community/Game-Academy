from copy import deepcopy
from numpy import linspace

from django.core.management.base import BaseCommand

from auctiongame.models import Answer, Result
from core.models import Session, Game

from auctiongame.apps import NAME


class Command(BaseCommand):
    help = "Updates the values required for the global_results page, to be run each time a new answer is submitted."

    def add_arguments(self, parser):
        parser.add_argument("--session", type=str, required=True)
        parser.add_argument("--game", type=str, required=True)

    def handle(self, *args, **options):
        if not options["session"]:
            self.stderr.write(
                "ERROR: you need to give the URL tag of a session with the --session argument"
            )
            return
        session = Session.objects.filter(url_tag=options["session"]).first()
        if not session:
            self.stderr.write(
                "ERROR: no session with URL tag {} has been found".format(
                    options["session"]
                )
            )
            return

        if not options["game"]:
            self.stderr.write(
                "ERROR: you need to give the URL tag of a game with the --game argument"
            )
            return
        game = Game.objects.filter(
            session=session, url_tag=options["game"], game_type=NAME
        ).first()
        if not game:
            self.stderr.write(
                "ERROR: no game with URL tag {} has been found".format(options["game"])
            )
            return

        all_answers = Answer.objects.filter(game=game)
        for answer in all_answers:
            answer.utility = answer.valuation - answer.bid
        Answer.objects.bulk_update(all_answers, ["utility"])

        global_highest_utility = None
        global_winner = None
        unique_auction_ids = all_answers.values_list('auction_id', flat=True).distinct()
        for auction_id in unique_auction_ids:
            answers = all_answers.filter(auction_id=auction_id, bid__isnull=False)
            if answers:
                bids = answers.values_list('bid', flat=True)
                bids_category_labels = linspace(
                    int(min(bids)),
                    int(max(bids)) + 1,
                    (int(max(bids)) + 1 - int(min(bids))) * 4 + 1,
                )
                bids_categories = {i: 0 for i in bids_category_labels}
                for bid in bids:
                    previous_label = bids_category_labels[0]
                    for label in bids_category_labels:
                        if label > bid:
                            break
                        previous_label = label
                    if previous_label is not None:
                        bids_categories[previous_label] += 1

                valuations = answers.values_list('valuation', flat=True)
                val_category_labels = range(min(valuations), max(valuations) + 1)
                val_categories = {i: 0 for i in val_category_labels}
                for val in valuations:
                    previous_label = bids_category_labels[0]
                    for label in bids_category_labels:
                        if label > val:
                            break
                        previous_label = label
                    if previous_label is not None:
                        val_categories[previous_label] += 1
                Result.objects.update_or_create(
                    game=game,
                    auction_id=auction_id,
                    defaults={
                        "histo_bids_js_data": "\n".join(["['{}', {}],".format(key, val)for key, val in bids_categories.items()]),
                        "histo_val_js_data": "\n".join(["['{}', {}],".format(key, val)for key, val in val_categories.items()])
                    }
                )

                highest_bid = None
                local_winners = None
                for answer in answers:
                    if highest_bid is None or answer.bid > highest_bid:
                        highest_bid = answer.bid
                        local_winners = [answer]
                    elif answer.bid == highest_bid:
                        local_winners.append(answer)
                    answer.winning_auction = False
                    answer.winning_global = False
                    answer.save()
                for answer in answers:
                    if answer not in local_winners:
                        answer.utility = 0
                        answer.save()
                winning_utility = local_winners[0].utility
                if winning_utility < 0:
                    new_local_winners = [
                        answer for answer in answers if answer not in local_winners
                    ]
                elif winning_utility == 0:
                    new_local_winners = list(answers)
                else:
                    new_local_winners = local_winners
                for answer in new_local_winners:
                    answer.winning_auction = True
                    answer.save()
                if new_local_winners:
                    new_winning_utility = new_local_winners[0].utility
                    if (
                        global_highest_utility is None
                        or new_winning_utility > global_highest_utility
                    ):
                        global_highest_utility = new_winning_utility
                        global_winner = deepcopy(new_local_winners)
                    elif new_winning_utility == global_highest_utility:
                        for answer in new_local_winners:
                            global_winner.append(answer)
        if global_winner is not None:
            for answer in global_winner:
                answer.winning_global = True
                answer.save()
