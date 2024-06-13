import csv

from core.models import Team, Player


def team_to_csv(writer, game):
    writer = csv.writer(writer)
    writer.writerow(
        [
            "name",
            "team_player_name",
            "player",
            "is_creator",
        ]
    )
    for team in Team.objects.filter(game=game):
        for player in team.players.all():
            writer.writerow(
                [
                    team.name,
                    team.team_player.name,
                    player.name,
                    player == team.creator
                ]
            )


def player_to_csv(writer, session):
    writer = csv.writer(writer)
    writer.writerow(
        [
            "player_name",
            "is_guest",
            "is_team_player",
        ]
    )
    for p in Player.objects.filter(session=session):
        writer.writerow(
            [
                p.name,
                p.is_guest,
                p.is_team_player
            ]
        )
