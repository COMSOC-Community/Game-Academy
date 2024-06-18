import random

from centipedegame.constants import CENTIPEDE_STRATEGIES
from centipedegame.models import Answer


def create_random_answers(game, players):
    answers = []
    for player in players:
        answers.append(
            Answer(
                game=game,
                player=player,
                strategy_as_p1=random.choice(CENTIPEDE_STRATEGIES),
                strategy_as_p2=random.choice(CENTIPEDE_STRATEGIES),
                motivation="Answer has been randomly generated",
            )
        )
    return Answer.objects.bulk_create(answers)
