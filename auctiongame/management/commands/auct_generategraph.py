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
        session = Session.objects.filter(url_tag=options["session"])
        if not session.exists():
            self.stderr.write(
                "ERROR: no session with URL tag {} has been found".format(
                    options["session"]
                )
            )
            return
        session = session.first()

        if not options["game"]:
            self.stderr.write(
                "ERROR: you need to give the URL tag of a game with the --game argument"
            )
            return
        game = Game.objects.filter(
            session=session, url_tag=options["game"], game_type=NAME
        )
        if not game.exists():
            self.stderr.write(
                "ERROR: no game with URL tag {} has been found".format(options["game"])
            )
            return
        game = game.first()

        try:
            game.result_auct
        except Result.DoesNotExist:
            result = Result.objects.create(
                game=game,
                histo_auct1_js_data="",
                histo_auct2_js_data="",
                histo_auct3_js_data="",
                histo_auct4_js_data="",
                histo_auct5_js_data="",
            )
            game.result_auct = result
            game.save()

        all_answers = Answer.objects.filter(game=game)
        for answer in all_answers:
            answer.utility = 10 + answer.auction_id - answer.bid
        Answer.objects.bulk_update(all_answers, ["utility"])

        global_highest_utility = None
        global_winner = None
        for auction_id in range(1, 6):
            answers = all_answers.filter(auction_id=auction_id, bid__isnull=False)
            if answers:
                bids = [answer.bid for answer in answers]
                if bids:
                    category_labels = linspace(
                        int(min(bids)),
                        int(max(bids)) + 1,
                        (int(max(bids)) + 1 - int(min(bids))) * 4 + 1,
                    )
                    categories = {i: 0 for i in category_labels}
                    for bid in bids:
                        previous_label = category_labels[0]
                        for label in category_labels:
                            if label > bid:
                                break
                            previous_label = label
                        if previous_label is not None:
                            categories[previous_label] += 1
                    attr_name = "histo_auct{}_js_data".format(auction_id)
                    setattr(
                        game.result_auct,
                        attr_name,
                        "\n".join(
                            [
                                "['{}', {}],".format(key, val)
                                for key, val in categories.items()
                            ]
                        ),
                    )
                    game.result_auct.save()

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
