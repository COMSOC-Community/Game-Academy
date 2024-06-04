from django.core.management.base import BaseCommand

from core.models import Session, Game
from iteprisonergame.apps import NAME
from iteprisonergame.automata import MooreMachine
from iteprisonergame.models import Answer


def itepris_graph_data(answer):
    if answer.number_states() < 100:
        automata = MooreMachine()
        automata.parse_from_answer(answer)
        return automata.json_data()


class Command(BaseCommand):
    help = "Computes the global_results of the IPD."

    def add_arguments(self, parser):
        parser.add_argument("--session", type=str, required=True)
        parser.add_argument("--game", type=str, required=True)

    def handle(self, IP_NAME=None, *args, **options):
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

        for answer in Answer.objects.filter(game=game):
            json_data = itepris_graph_data(answer)
            if json_data:
                answer.graph_json_data = json_data
                answer.save()
