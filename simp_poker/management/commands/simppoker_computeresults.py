import numpy as np
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
    pj = int(4 - 3 * answer.prob_p2_king - 3 * answer.prob_p2_queen > 0)
    qq = int(3 * answer.prob_p1_jack - answer.prob_p1_king > 0)
    return np.array([1, 1, pj, 1, qq, 0])


def compute_global_best_response(answers):
    pj_coeff = sum(4 - 3 * answer.prob_p2_king - 3 * answer.prob_p2_queen for answer in answers)
    qq_coeff = sum(3 * answer.prob_p1_jack - answer.prob_p1_king for answer in answers)
    return np.array([1, 1, int(pj_coeff > 0), 1, int(qq_coeff > 0), 0])


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

        ## Compute all the scores for the answers
        optimal_strategy = Answer(
            prob_p1_king=1,
            prob_p1_queen=1,
            prob_p1_jack=1 / 3,
            prob_p2_king=1,
            prob_p2_queen=1 / 3,
            prob_p2_jack=0
        )
        rr_scores = {a: 0 for a in answers}
        rr_with_opt_scores = {}
        scores_against_opt = {}
        best_responses = {}
        score_against_best_response = {}
        optimal_strategy_score = 0
        for i in range(len(answers)):
            answer = answers[i]

            # Round Robin tournament
            for j in range(i + 1, len(answers)):
                opponent = answers[j]
                total_expected_u_answer = expected_utility(answer, opponent)
                rr_scores[answer] += total_expected_u_answer
                rr_scores[opponent] -= total_expected_u_answer

            # Performance against optimum
            score_against_opt = expected_utility(answer, optimal_strategy)
            optimal_strategy_score -= score_against_opt
            scores_against_opt[answer] = score_against_opt
            rr_with_opt_scores[answer] = rr_scores[answer] + score_against_opt

            # Best response against the strategy
            best_response = compute_best_response(answer)
            best_response_strat = Answer(
                prob_p1_king=best_response[0],
                prob_p1_queen=best_response[1],
                prob_p1_jack=best_response[2],
                prob_p2_king=best_response[3],
                prob_p2_queen=best_response[4],
                prob_p2_jack=best_response[5]
            )
            best_responses[answer] = best_response
            score_against_best_response[answer] = expected_utility(answer, best_response_strat)
        unique_rr_scores = sorted(set(rr_scores.values()), reverse=True)
        all_rr_with_opt_scores = set(rr_with_opt_scores.values())
        all_rr_with_opt_scores.add(optimal_strategy_score)
        unique_rr_with_opt_scores = sorted(all_rr_with_opt_scores, reverse=True)

        num_players = len(rr_scores)
        for answer in answers:
            rr_score = rr_scores[answer]
            answer.round_robin_score = rr_score / (max(1, num_players - 1))
            answer.round_robin_position = unique_rr_scores.index(rr_score) + 1
            rr_score_with_opt = rr_with_opt_scores[answer]
            answer.round_robin_with_opt_score = rr_score_with_opt / num_players
            answer.round_robin_with_opt_position = unique_rr_with_opt_scores.index(rr_score_with_opt) + 1
            score_against_opt = scores_against_opt[answer]
            answer.score_against_optimum = score_against_opt
            answer.winner_against_optimum = score_against_opt >= 0
            answer.best_response = ','.join(float_formatter(v, num_digits=5) for v in best_responses[answer])
            answer.score_against_best_response = score_against_best_response[answer]
            answer.save()

        global_best_response = compute_global_best_response(answers)
        global_best_response_answer = Answer(
            prob_p1_king=global_best_response[0],
            prob_p1_queen=global_best_response[1],
            prob_p1_jack=global_best_response[2],
            prob_p2_king=global_best_response[3],
            prob_p2_queen=global_best_response[4],
            prob_p2_jack=global_best_response[5]
        )
        global_best_response_score = sum(expected_utility(global_best_response_answer, a) for a in answers) / len(answers)
        Result.objects.update_or_create(
            game=game,
            defaults={
                "optimal_strategy_round_robin_score": optimal_strategy_score / max(1, num_players),
                "optimal_strategy_round_robin_position": unique_rr_with_opt_scores.index(optimal_strategy_score) + 1,
                "global_best_response": ','.join(float_formatter(v, num_digits=5) for v in global_best_response),
                "global_best_response_rr_score": global_best_response_score,
            }
        )
