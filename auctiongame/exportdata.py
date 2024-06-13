import csv

from auctiongame.models import Answer


def answers_to_csv(writer, game):
    writer = csv.writer(writer)
    writer.writerow(
        [
            "player_name",
            "is_team_player",
            "auction_id",
            "bid",
            "utility",
            "winning_auction",
            "winning_global",
            "motivation"
        ]
    )
    for answer in Answer.objects.filter(game=game):
        writer.writerow([
            answer.player.name,
            answer.player.is_team_player,
            answer.auction_id,
            answer.bid,
            answer.utility,
            answer.winning_auction,
            answer.winning_global,
            answer.motivation
        ])
