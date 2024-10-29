import random

from auctiongame.models import Answer
from auctiongame.samplers import ALL_SAMPLERS
from core.utils import float_formatter


def create_random_answers(game, players):
    answers = []
    for player in players:
        auction_id = random.randint(1, game.auction_setting.number_auctions)
        valuation = ALL_SAMPLERS[game.auction_setting.valuation_sampler].sample(auction_id)
        answers.append(
            Answer(
                game=game,
                player=player,
                auction_id=auction_id,
                valuation=valuation,
                bid=float_formatter(random.uniform(valuation - 3, valuation), num_digits=5),
                motivation="Answer has been randomly generated",
            )
        )
    return Answer.objects.bulk_create(answers)
