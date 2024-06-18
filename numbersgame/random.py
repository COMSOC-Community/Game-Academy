import random

from core.utils import float_formatter
from numbersgame.models import Answer


def create_random_answers(game, players):
    lower_bound = game.numbers_setting.lower_bound
    upper_bound = game.numbers_setting.upper_bound
    answers = []
    for player in players:
        raw_answer = random.random() * (upper_bound - lower_bound) + lower_bound
        answers.append(
            Answer(
                game=game,
                player=player,
                answer=float_formatter(raw_answer, num_digits=5),
                motivation="Answer has been randomly generated",
            )
        )
    return Answer.objects.bulk_create(answers)
