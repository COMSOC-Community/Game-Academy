import csv

from centipedegame.models import Answer, Setting


def answers_to_csv(writer, game):
    writer = csv.writer(writer)
    writer.writerow(
        [
            "player_name",
            "is_team_player",
            "strategy_as_p1",
            "strategy_as_p2",
            "avg_score_as_p1",
            "avg_score_as_p2",
            "avg_score",
            "winning",
            "motivation",
            "submission_time"
        ]
    )
    for answer in Answer.objects.filter(game=game):
        writer.writerow([
            answer.player.name,
            answer.player.is_team_player,
            answer.strategy_as_p1,
            answer.strategy_as_p2,
            answer.avg_score_as_p1,
            answer.avg_score_as_p2,
            answer.avg_score,
            answer.winning,
            answer.motivation,
            answer.submission_time
        ])


def settings_to_csv(writer, game):
    setting = None
    try:
        setting = game.centi_setting
    except Setting.DoesNotExist:
        pass
    if setting:
        writer = csv.writer(writer)
        writer.writerow(
            [
                "payoff_d_p1",
                "payoff_d_p2",
                "payoff_rd_p1",
                "payoff_rd_p2",
                "payoff_rrd_p1",
                "payoff_rrd_p2",
                "payoff_rrrd_p1",
                "payoff_rrrd_p2",
                "payoff_rrrr_p1",
                "payoff_rrrr_p2"
            ]
        )
        writer.writerow([
            setting.payoff_d_p1,
            setting.payoff_d_p2,
            setting.payoff_rd_p1,
            setting.payoff_rd_p2,
            setting.payoff_rrd_p1,
            setting.payoff_rrd_p2,
            setting.payoff_rrrd_p1,
            setting.payoff_rrrd_p2,
            setting.payoff_rrrr_p1,
            setting.payoff_rrrr_p2,
        ])
