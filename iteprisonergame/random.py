import random
import string

from iteprisonergame.models import Answer


def create_random_answers(game, players):
    answers = []
    for player in players:
        number_of_states = random.randint(1, 20)
        automata = ""
        states_to_populate = [0]
        populated_states = set()
        while len(states_to_populate) > 0:
            state = states_to_populate.pop()
            if state not in populated_states:
                action = random.choice(("C", "D"))
                next_state_C = random.choice(range(number_of_states))
                if next_state_C not in populated_states:
                    states_to_populate.append(next_state_C)
                next_state_D = random.choice(range(number_of_states))
                if next_state_D not in populated_states:
                    states_to_populate.append(next_state_D)
                automata += f"{state}: {action}, {next_state_C}, {next_state_D}\n"
                populated_states.add(state)
        answers.append(
            Answer(
                game=game,
                player=player,
                automata=automata,
                initial_state="0",
                motivation="Answer has been randomly generated",
                name=''.join(random.choices(string.ascii_letters + string.digits, k=5))
            )
        )
    return Answer.objects.bulk_create(answers)
