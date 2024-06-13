import csv

from numbersgame.models import Answer, Setting


def answers_to_csv(writer, game):
    writer = csv.writer(writer)
    writer.writerow(
        [
            "player_name",
            "is_team_player",
            "answer",
            "motivation",
            "gap",
            "winner",
            "submission_time"
        ]
    )
    for answer in Answer.objects.filter(game=game):
        writer.writerow([
            answer.player.name,
            answer.player.is_team_player,
            answer.answer,
            answer.motivation,
            answer.gap,
            answer.winner,
            answer.submission_time
        ])


def settings_to_csv(writer, game):
    setting = None
    try:
        setting = game.numbers_setting
    except Setting.DoesNotExist:
        pass
    if setting:
        writer = csv.writer(writer)
        writer.writerow(
            [
                "lower_bound",
                "upper_bound",
                "factor",
                "factor_display",
                "histogram_bin_size",
            ]
        )
        writer.writerow([
            setting.lower_bound,
            setting.upper_bound,
            setting.factor,
            setting.factor_display,
            setting.histogram_bin_size,
        ])
