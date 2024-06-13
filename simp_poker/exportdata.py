import csv

from simp_poker.models import Answer


def answers_to_csv(writer, game):
    writer = csv.writer(writer)
    writer.writerow(
        [
            "player_name",
            "is_team_player",
            "prob_p1_king",
            "prob_p1_queen",
            "prob_p1_jack",
            "prob_p2_king",
            "prob_p2_queen",
            "prob_p2_jack",
            "motivation",
            "round_robin_score",
            "round_robin_position",
            "round_robin_with_opt_score",
            "round_robin_with_opt_position",
            "score_against_optimum",
            "winner_against_optimum",
            "best_response",
            "score_against_best_response",
            "submission_time"
        ]
    )
    for answer in Answer.objects.filter(game=game):
        writer.writerow([
            answer.player.name,
            answer.player.is_team_player,
            answer.prob_p1_king,
            answer.prob_p1_queen,
            answer.prob_p1_jack,
            answer.prob_p2_king,
            answer.prob_p2_queen,
            answer.prob_p2_jack,
            answer.motivation,
            answer.round_robin_score,
            answer.round_robin_position,
            answer.round_robin_with_opt_score,
            answer.round_robin_with_opt_position,
            answer.score_against_optimum,
            answer.winner_against_optimum,
            answer.best_response,
            answer.score_against_best_response,
            answer.submission_time
        ])
