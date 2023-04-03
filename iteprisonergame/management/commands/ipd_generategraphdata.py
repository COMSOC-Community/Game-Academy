from django.core.management.base import BaseCommand

from core.models import Session, Game
from iteprisonergame.apps import IPD_ROUNDS, IPD_PAYOFFS, IPD_NAME
from iteprisonergame.automata import MooreMachine, fight
from iteprisonergame.models import Answer, Score


class Command(BaseCommand):
    help = 'Computes the results of the IPD.'

    def add_arguments(self, parser):
        parser.add_argument('--session', type=str, required=True)
        parser.add_argument('--game', type=str, required=True)

    def handle(self, IP_NAME=None, *args, **options):
        if not options['session']:
            print('ERROR: you need to give the URL tag of a session with the --session argument')
            return
        session = Session.objects.filter(slug_name=options['session'])
        if not session.exists():
            print('ERROR: no session with URL tag {} has been found'.format(options['session']))
            return
        session = session.first()

        if not options['game']:
            print('ERROR: you need to give the URL tag of a game with the --game argument')
            return
        game = Game.objects.filter(session=session, url_tag=options['game'], game_type=IPD_NAME)
        if not game.exists():
            print('ERROR: no game with URL tag {} has been found'.format(options['game']))
            return
        game = game.first()

        for answer in Answer.objects.filter(game=game):
            nodes = []
            links = []
            for line in answer.automata.strip().split("\n"):
                state, transition = line.strip().split(":")
                state = state.strip()
                action, next_state_coop, next_state_def = transition.strip().split(',')
                if state == answer.initial_state.strip():
                    nodes.append({"id": state, "name": action.strip()})
                    links.append({"source": state, "target": next_state_coop, "label": "C"})
                    links.append({"source": state, "target": next_state_def, "label": "D"})
            json_data = '{nodes: ['
            for node in nodes:
                json_data += '{id: ' + str(node["id"].strip()) + ',name: "' + str(node["name"]).strip() + '"},'
            json_data = json_data[:-1] + '],edges: ['
            for link in links:
                json_data += '{source: ' + str(link["source"].strip()) + ',target: ' + \
                             str(link["target"].strip()) + ',label: "' + str(link["label"].strip()) + '"},'
            json_data = json_data[:-1] + ']}'
            answer.graph_json_data = json_data
            answer.save()
