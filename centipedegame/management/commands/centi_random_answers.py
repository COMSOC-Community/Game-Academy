import random
import string

from django.core import management
from django.core.management.base import BaseCommand

from centipedegame.constants import CENTIPEDE_STRATEGIES
from centipedegame.models import Answer
from core.models import Session, Game, Player, CustomUser

from centipedegame.apps import NAME


class Command(BaseCommand):
    help = "Generates random answers for the centipede game."

    def add_arguments(self, parser):
        parser.add_argument("n", type=int)
        parser.add_argument("--session", type=str, required=True)
        parser.add_argument("--game", type=str, required=True)

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
        game = Game.objects.filter(
            session=session, url_tag=options["game"], game_type=NAME
        )
        if not game.exists():
            self.stderr.write(
                "ERROR: no game with URL tag {} has been found".format(options["game"])
            )
            return
        game = game.first()

        num_answers = options['n']
        if num_answers <= 0:
            self.stderr.write(
                "The number of random answers to generate has to be at least 1."
            )
            return

        for _ in range(num_answers):
            player_name_prefix = "RANDOM_PLAYER_CENTI_"
            player_name = player_name_prefix + "a"
            while CustomUser.objects.filter(username=player_name).exists() or Player.objects.filter(name=player_name).exists():
                player_name = player_name_prefix + ''.join(random.choices(string.ascii_letters + string.digits, k=15))
            user = CustomUser.objects.create_user(
                player_name,
                password="random_centi_player_password"
            )
            player = Player.objects.create(
                user=user,
                name=player_name,
                session=session
            )
            Answer.objects.create(
                game=game,
                player=player,
                strategy_as_p1=random.choice(CENTIPEDE_STRATEGIES),
                strategy_as_p2=random.choice(CENTIPEDE_STRATEGIES),
                motivation="Answer has been randomly generated"
            )

        self.stdout.write(
            f"SUCCESS: {num_answers} random answers have been generated!"
        )

        management.call_command(
            "centi_computescores",
            session=session.url_tag,
            game=game.url_tag
        )
