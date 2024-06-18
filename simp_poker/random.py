import random

from core.utils import float_formatter
from simp_poker.models import Answer


def create_random_answers(game, players):
    answers = []
    for player in players:
        answers.append(
            Answer(
                game=game,
                player=player,
                prob_p1_king=float_formatter(random.random(), num_digits=5),
                prob_p1_queen=float_formatter(random.random(), num_digits=5),
                prob_p1_jack=float_formatter(random.random(), num_digits=5),
                prob_p2_king=float_formatter(random.random(), num_digits=5),
                prob_p2_queen=float_formatter(random.random(), num_digits=5),
                prob_p2_jack=float_formatter(random.random(), num_digits=5),
                motivation="Answer has been randomly generated",
            )
        )
    return Answer.objects.bulk_create(answers)
