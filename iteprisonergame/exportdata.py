import csv

from goodbadgame.models import Answer
from iteprisonergame.models import Setting


def answers_to_csv(writer, game):
    writer = csv.writer(writer)
    writer.writerow(
        [
            "player_name",
            "is_team_player",
            "answer_name",
            "automata",
            "initial_state",
            "motivation",
            "avg_score",
            "winner",
            "submission_time"
        ]
    )
    for answer in Answer.objects.filter(game=game):
        writer.writerow([
            answer.player.name,
            answer.player.is_team_player,
            answer.name,
            answer.automata,
            answer.initial_state,
            answer.motivation,
            answer.avg_score,
            answer.winner,
            answer.submission_time
        ])


def settings_to_csv(writer, game):
    setting = None
    try:
        setting = game.itepris_setting
    except Setting.DoesNotExist:
        pass
    if setting:
        writer = csv.writer(writer)
        writer.writerow(
            [
                "num_repetitions",
                "payoff_high",
                "payoff_medium",
                "payoff_low",
                "payoff_tiny",
                "forbidden_strategies"
            ]
        )
        writer.writerow([
            setting.num_repetitions,
            setting.payoff_high,
            setting.payoff_medium,
            setting.payoff_low,
            setting.payoff_tiny,
            setting.forbidden_strategies,
        ])
