import random
import string

from django.core import management
from django.core.management.base import BaseCommand

from iteprisonergame.models import Answer
from core.models import Session, Game, Player, CustomUser

from iteprisonergame.apps import NAME
from core.utils import float_formatter


class Command(BaseCommand):
    help = "Generates random answers for the auction game."

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
            number_of_states = random.randint(1, 20)
            automata = ""
            states_to_populate = [0]
            populated_states = set()
            while len(states_to_populate) > 0:
                state = states_to_populate.pop()
                if state not in populated_states:
                    action = random.choice(("C", "D"))
                    next_state_C = random.choice(range(number_of_states))
                    if next_state_C not in populated_states:
                        states_to_populate.append(next_state_C)
                    next_state_D = random.choice(range(number_of_states))
                    if next_state_D not in populated_states:
                        states_to_populate.append(next_state_D)
                    automata += f"{state}: {action}, {next_state_C}, {next_state_D}\n"
                    populated_states.add(state)
            Answer.objects.create(
                game=game,
                player=player,
                automata=automata,
                initial_state="0",
                motivation="Answer has been randomly generated"
            )

        self.stdout.write(
            f"SUCCESS: {num_answers} random answers have been generated!"
        )

        management.call_command(
            "ipd_computeresults",
            session=session.url_tag,
            game=game.url_tag
        )
        management.call_command(
            "ipd_generategraphdata",
            session=session.url_tag,
            game=game.url_tag
        )
