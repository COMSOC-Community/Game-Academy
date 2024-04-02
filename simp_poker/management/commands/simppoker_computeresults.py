from django.core.management.base import BaseCommand

from core.models import Session, Game
from core.utils import float_formatter
from simp_poker.apps import NAME
from simp_poker.models import Answer, Result


def expected_utility_fix_roles(answer1, answer2):
    pK = answer1.prob_p1_king
    pQ = answer1.prob_p1_queen
    pJ = answer1.prob_p1_jack
    qK = answer2.prob_p2_king
    qQ = answer2.prob_p2_queen
    qJ = answer2.prob_p2_jack
    # euKQ = 2 * pK * qQ + 1 * pK * (1 - qQ) - 1 * (1 - pK)
    euKQ = pK * qQ + 2 * pK - 1
    # euKJ = 2 * pK * qJ + 1 * pK * (1 - qJ) - 1 * (1 - pK)
    euKJ = pK * qJ + 2 * pK - 1
    # euQJ = 2 * pQ * qJ + 1 * pQ * (1 - qJ) - 1 * (1 - pQ)
    euQJ = pQ * qJ + 2 * pQ - 1
    # euQK = -2 * pQ * qK + 1 * pQ * (1 - qK) - 1 * (1 - pQ)
    euQK = -3 * pQ * qK + 2 * pQ - 1
    # euJK = -2 * pJ * qK + 1 * pJ * (1 - qK) - 1 * (1 - pJ)
    euJK = -3 * pJ * qK + 2 * pJ - 1
    # euJQ = -2 * pJ * qQ + 1 * pJ * (1 - qQ) - 1 * (1 - pJ)
    euJQ = -3 * pJ * qQ + 2 * pJ - 1
    return round((euKQ + euKJ + euQJ + euQK + euJK + euJQ) / 6, 5)


def expected_utility(answer1, answer2):
    return (expected_utility_fix_roles(answer1, answer2) - expected_utility_fix_roles(answer2, answer1)) / 2


def compute_best_response(answer):
    from mip import Model, maximize

    m = Model()
    pq = m.add_var("pq", lb=0, ub=1)  # Force to 1 here!
    pj = m.add_var("pj", lb=0, ub=1)
    qq = m.add_var("pj", lb=0, ub=1)
    m.objective = maximize(
        pq * (4 + answer.prob_p2_jack - 3 * answer.prob_p2_king) -
        3 * pj * (4 + answer.prob_p2_king + answer.prob_p2_queen) -
        qq * (answer.prob_p1_king - 3 * answer.prob_p1_jack)
    )
    m.optimize()
    return 1, pq.x, pj.x, 1, qq.x, 0


class Command(BaseCommand):
    help = "Computes the results of the simplified poker game."

    def add_arguments(self, parser):
        parser.add_argument("--session", type=str, required=True)
        parser.add_argument("--game", type=str, required=True)

    def handle(self, IP_NAME=None, *args, **options):
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
        answers = list(Answer.objects.filter(game=game))
        total_scores = {a: 0 for a in answers}
        for i in range(len(answers)):
            answer = answers[i]
            for j in range(i + 1, len(answers)):
                opponent = answers[j]
                total_expected_u_answer = expected_utility(answer, opponent)
                total_scores[answer] += total_expected_u_answer
                total_scores[opponent] -= total_expected_u_answer

        optimal_strategy = Answer(
            prob_p1_king=1,
            prob_p1_queen=1,
            prob_p1_jack=1 / 3,
            prob_p2_king=1,
            prob_p2_queen=1 / 3,
            prob_p2_jack=0
        )

        best_answer_round_robin = None
        best_score_round_robin = None
        num_players = len(total_scores)
        optimal_strategy_score = 0
        best_answer_against_opt = None
        best_score_against_opt = None
        for answer, score in total_scores.items():
            answer.round_robin_score = score / (max(1, num_players - 1))
            score_against_opt = expected_utility(answer, optimal_strategy)
            optimal_strategy_score -= score_against_opt

            best_response = compute_best_response(answer)
            best_response_strat = Answer(
                prob_p1_king=best_response[0],
                prob_p1_queen=best_response[1],
                prob_p1_jack=best_response[2],
                prob_p2_king=best_response[3],
                prob_p2_queen=best_response[4],
                prob_p2_jack=best_response[5]
            )
            score_against_best = expected_utility(answer, best_response_strat)

            answer.score_against_optimum = score_against_opt
            answer.round_robin_with_opt_score = (score + score_against_opt) / num_players
            answer.winner = False
            answer.best_response = "(" + ", ".join(float_formatter(v, num_digits=5) for v in best_response) + ")"
            answer.score_against_best_response = score_against_best
            answer.save()

            if best_score_round_robin is None or score > best_score_round_robin:
                best_score_round_robin = score
                best_answer_round_robin = [answer]
            elif score == best_score_round_robin:
                best_answer_round_robin.append(answer)

            if best_score_against_opt is None or score_against_opt > best_score_against_opt:
                best_score_against_opt = score_against_opt
                best_answer_against_opt = [answer]
            elif score_against_opt == best_score_against_opt:
                best_answer_against_opt.append(answer)

        if best_answer_round_robin:
            for answer in best_answer_round_robin:
                answer.round_robin_winner = True
                answer.save()

        if best_answer_against_opt:
            for answer in best_answer_against_opt:
                answer.winner_against_optimum = True
                answer.save()

        Result.objects.update_or_create(
            game=game,
            defaults={
                "optimal_strategy_score": optimal_strategy_score / max(1, num_players)
            }
        )
