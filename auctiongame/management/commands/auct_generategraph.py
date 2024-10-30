import numpy as np
from django.db import models, transaction
from django.core.management.base import BaseCommand
from auctiongame.models import Answer, Result
from core.models import Session, Game
from auctiongame.apps import NAME


class Command(BaseCommand):
    help = "Updates values for the global_results page. Run each time a new answer is submitted."

    def add_arguments(self, parser):
        parser.add_argument("--session", type=str, required=True)
        parser.add_argument("--game", type=str, required=True)

    def handle(self, *args, **options):
        # Retrieve session and game
        session = Session.objects.filter(url_tag=options["session"]).first()
        if not session:
            self.stderr.write(f"ERROR: No session found with URL tag {options['session']}")
            return

        game = Game.objects.filter(session=session, url_tag=options["game"], game_type=NAME).first()
        if not game:
            self.stderr.write(f"ERROR: No game found with URL tag {options['game']}")
            return

        # Retrieve all answers and compute initial utilities
        all_answers = Answer.objects.filter(game=game)
        all_answers.update(utility=models.F('valuation') - models.F('bid'))  # Utility bulk update

        global_highest_utility = None
        global_winner = []

        results_to_update = []
        results_to_create = []
        answers_to_update = []

        unique_auction_ids = all_answers.values_list("auction_id", flat=True).distinct()
        for auction_id in unique_auction_ids:
            # Get or initialize Result object
            result, created = Result.objects.get_or_create(game=game, auction_id=auction_id)

            answers = all_answers.filter(auction_id=auction_id, bid__isnull=False)

            if not answers:
                continue

            # Process histogram data for bids
            bids = np.array(answers.filter(auction_id=auction_id).values_list("bid", flat=True))
            bid_lb, bid_up = int(bids.min()), int(bids.max()) + 1
            bid_bins, bid_counts = np.histogram(bids, bins=np.linspace(bid_lb, bid_up,
                                                                       (bid_up - bid_lb) * 4 + 1))
            result.histo_bids_js_data = "\n".join(
                [f"['{count}', {bin}]," for bin, count in zip(bid_bins, bid_counts)])

            # Process histogram data for valuations
            valuations = np.array(
                answers.filter(auction_id=auction_id).values_list("valuation", flat=True))
            val_min, val_max = valuations.min(), valuations.max()
            val_bins, val_counts = np.histogram(valuations, bins=np.arange(val_min, val_max + 2))
            result.histo_val_js_data = "\n".join(
                [f"['{count}', {bin}]," for bin, count in zip(val_bins, val_counts)])

            if created:
                results_to_create.append(result)
            else:
                results_to_update.append(result)

            # Determine auction winners
            highest_bid = bids.max()
            local_winners = [a for a in answers if a.bid == highest_bid]
            for answer in answers:
                answer.winning_auction = answer in local_winners
                answer.utility = answer.utility if answer in local_winners else 0
                answers_to_update.append(answer)

            # Global winner selection
            winning_utility = local_winners[0].utility
            if global_highest_utility is None or winning_utility > global_highest_utility:
                global_highest_utility = winning_utility
                global_winner = local_winners
            elif winning_utility == global_highest_utility:
                global_winner.extend(local_winners)

            # Update all global winner flags and save updates in bulk
        for answer in global_winner:
            answer.winning_global = True
            answers_to_update.append(answer)

        # Save all results in a single transaction
        with transaction.atomic():
            Result.objects.bulk_create(results_to_create, ignore_conflicts=True)
            Result.objects.bulk_update(results_to_update,
                                       ["histo_bids_js_data", "histo_val_js_data"])
            Answer.objects.bulk_update(answers_to_update,
                                       ["utility", "winning_auction", "winning_global"])
