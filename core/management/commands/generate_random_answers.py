import random
import string

from django.core import management
from django.core.management.base import BaseCommand

from auctiongame.models import Answer
from core.models import Session, Game, Player, CustomUser

from auctiongame.apps import NAME
from core.random import random_players
from core.utils import float_formatter


class Command(BaseCommand):
    help = "Generates random answers for the auction game."

    def add_arguments(self, parser):
        parser.add_argument("n", type=int)
        parser.add_argument("--session", type=str, required=True)
        parser.add_argument("--game", type=str, required=True)
        parser.add_argument("--run_command", action="store_true")

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

        players = random_players(session, num_answers)


        for _ in range(num_answers):
            player_name_prefix = "RANDOM_PLAYER_AUCT_"
            player_name = player_name_prefix + "a"
            while CustomUser.objects.filter(username=player_name).exists() or Player.objects.filter(name=player_name).exists():
                player_name = player_name_prefix + ''.join(random.choices(string.ascii_letters + string.digits, k=15))
            user = CustomUser.objects.create_user(
                player_name,
                password="random_auct_player_password"
            )
            player = Player.objects.create(
                user=user,
                name=player_name,
                session=session
            )
            auction_id = random.randint(1, 5)
            Answer.objects.create(
                game=game,
                player=player,
                auction_id=auction_id,
                bid=float_formatter(random.random() * (auction_id + 10), num_digits=5),
                motivation="Answer has been randomly generated"
            )

        self.stdout.write(
            f"SUCCESS: {num_answers} random answers have been generated!"
        )

        if options["run_command"]:
            management.call_command(
                "auct_generategraph",
                session=session.url_tag,
                game=game.url_tag
            )
