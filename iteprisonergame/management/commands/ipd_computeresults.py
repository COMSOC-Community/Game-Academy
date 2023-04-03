from django.core.management.base import BaseCommand

from core.models import Session, Game
from iteprisonergame.apps import IPD_ROUNDS, IPD_PAYOFFS, IPD_NAME
from iteprisonergame.automata import MooreMachine, fight
from iteprisonergame.models import Answer, Score


class Command(BaseCommand):
    help = 'Computes the results of the IPD.'

    def add_arguments(self, parser):
        parser.add_argument('--session', type=str, required=True)
        parser.add_argument('--game', type=str, required=True)

    def handle(self, IP_NAME=None, *args, **options):
        if not options['session']:
            print('ERROR: you need to give the URL tag of a session with the --session argument')
            return
        session = Session.objects.filter(slug_name=options['session'])
        if not session.exists():
            print('ERROR: no session with URL tag {} has been found'.format(options['session']))
            return
        session = session.first()

        if not options['game']:
            print('ERROR: you need to give the URL tag of a game with the --game argument')
            return
        game = Game.objects.filter(session=session, url_tag=options['game'], game_type=IPD_NAME)
        if not game.exists():
            print('ERROR: no game with URL tag {} has been found'.format(options['game']))
            return
        game = game.first()

        ans_automatas = []
        for answer in Answer.objects.filter(game=game):
            automata = MooreMachine()
            automata.initial_state = answer.initial_state.strip()
            for line in answer.automata.strip().split("\n"):
                state, transition = line.strip().split(":")
                state = state.strip()
                action, next_state_coop, next_state_def = transition.strip().split(',')
                automata.add_transition(state, "C", next_state_coop.strip())
                automata.add_transition(state, "D", next_state_def.strip())
                automata.add_outcome(state, action.strip())
            ans_automatas.append((answer, automata))

        total_scores = {answer: 0 for answer, _ in ans_automatas}
        for i in range(len(ans_automatas)):
            answer, ans_automata = ans_automatas[i]
            for j in range(i + 1, len(ans_automatas)):
                opponent, opp_automata = ans_automatas[j]
                for round_number in IPD_ROUNDS:
                    outcomes_ans, outcomes_opp = fight(ans_automata, opp_automata, round_number)
                    score1 = 0
                    score2 = 0
                    for round_index in range(round_number):
                        s1, s2 = IPD_PAYOFFS[(outcomes_ans[round_index], outcomes_opp[round_index])]
                        score1 += s1
                        score2 += s2
                    total_scores[answer] += score1
                    total_scores[opponent] += score2
                    Score.objects.update_or_create(
                        answer=answer,
                        opponent=opponent,
                        number_round=round_number,
                        defaults={
                            'score': score1
                        }
                    )
                    Score.objects.update_or_create(
                        answer=opponent,
                        opponent=answer,
                        number_round=round_number,
                        defaults={
                            'score': score2
                        }
                    )
        best_answer = None
        best_score = None
        for answer, score in total_scores.items():
            answer.total_score = score
            answer.winner = False
            answer.save()
            if best_score is None or score > best_score:
                best_score = score
                best_answer = [answer]
            elif score == best_score:
                best_answer.append(answer)
        for answer in best_answer:
            answer.winner = True
            answer.save()

