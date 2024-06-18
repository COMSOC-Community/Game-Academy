import random

from auctiongame.models import Answer
from core.utils import float_formatter


def create_random_answers(game, players):
    answers = []
    for player in players:
        auction_id = random.randint(1, 5)
        answers.append(
            Answer(
                game=game,
                player=player,
                auction_id=auction_id,
                bid=float_formatter(random.random() * (auction_id + 10), num_digits=5),
                motivation="Answer has been randomly generated",
            )
        )
    return Answer.objects.bulk_create(answers)
