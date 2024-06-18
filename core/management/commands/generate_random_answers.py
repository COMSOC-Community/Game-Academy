from django.core import management
from django.core.management.base import BaseCommand

from core.models import Session, Game
from core.random import create_random_players, create_random_teams


class Command(BaseCommand):
    help = "Generates random answers for the auction game."

    def add_arguments(self, parser):
        parser.add_argument("n", type=int)
        parser.add_argument("--session", type=str, required=True)
        parser.add_argument("--game", type=str, required=True)
        parser.add_argument("--run_management", action="store_true")

    def handle(self, *args, **options):
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
        game = Game.objects.filter(session=session, url_tag=options["game"])
        if not game.exists():
            self.stderr.write(
                "ERROR: no game with URL tag {} has been found".format(options["game"])
            )
            return
        game = game.first()

        num_answers = options["n"]
        if num_answers <= 0:
            self.stderr.write(
                "The number of random answers to generate has to be at least 1."
            )
            return

        random_answers_func = game.game_config().random_answers_func
        if random_answers_func is None:
            self.stderr.write(
                "ERROR: The game is not configured to generate random answers."
            )
            return

        if game.needs_teams:
            teams = create_random_teams(session, game, num_answers)
            players = [t.team_player for t in teams]
        else:
            players = create_random_players(session, num_answers)
        answers = random_answers_func(game, players)

        self.stdout.write(
            f"SUCCESS: {len(answers)} random answers have been generated!"
        )

        if options["run_management"]:
            if game.game_config().management_commands is not None:
                for cmd_name in game.game_config().management_commands:
                    management.call_command(
                        cmd_name,
                        session=session.url_tag,
                        game=game.url_tag,
                        stdout=self.stdout,
                    )
