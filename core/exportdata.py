import csv

from core.models import Team, Player, Game


def session_to_csv(writer, session):
    """Exports a Session to a CSV file. The buffer is passed as argument to be able to write either
    files or request (or any buffer)."""
    writer = csv.writer(writer)
    writer.writerow(
        [
            "url_tag",
            "name",
            "long_name",
            "show_create_account",
            "show_guest_login",
            "show_user_login",
            "visible",
            "admins",
            "super_admins",
            "game_after_logging",
        ]
    )
    writer.writerow(
        [
            session.url_tag,
            session.name,
            session.long_name,
            session.show_create_account,
            session.show_guest_login,
            session.show_user_login,
            session.visible,
            ";".join(a.username for a in session.admins.all()),
            ";".join(a.username for a in session.super_admins.all()),
            session.game_after_logging,
        ]
    )


def team_to_csv(writer, game):
    """Exports the teams of a game to a CSV file. The buffer is passed as argument to be able to
    write either files or request (or any buffer)."""
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
                [team.name, team.team_player.name, player.name, player == team.creator]
            )


def player_to_csv(writer, session):
    """Exports the players of a session to a CSV file. The buffer is passed as argument to be able
    to write either files or request (or any buffer)."""
    writer = csv.writer(writer)
    writer.writerow(
        [
            "player_name",
            "is_guest",
            "is_team_player",
        ]
    )
    for p in Player.objects.filter(session=session):
        writer.writerow([p.name, p.user.is_guest_player, p.is_team_player])


def games_to_csv(writer, session):
    """Exports the games of a session to a CSV file. The buffer is passed as argument to be able to
    write either files or request (or any buffer)."""
    writer = csv.writer(writer)
    writer.writerow(
        [
            "name",
            "url_tag",
            "playable",
            "visible",
            "results_visible",
            "needs_teams",
            "description",
            "illustration_path",
            "ordering_priority",
            "run_management_after_submit",
            "initial_view",
            "view_after_submit",
        ]
    )
    for g in Game.objects.filter(session=session):
        writer.writerow(
            [
                g.name,
                g.url_tag,
                g.playable,
                g.visible,
                g.results_visible,
                g.needs_teams,
                g.description,
                g.illustration_path,
                g.ordering_priority,
                g.run_management_after_submit,
                g.initial_view,
                g.view_after_submit,
            ]
        )
