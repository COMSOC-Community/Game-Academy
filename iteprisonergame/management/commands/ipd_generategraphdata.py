from django.core.management.base import BaseCommand

from core.models import Session, Game
from iteprisonergame.apps import NAME
from iteprisonergame.models import Answer


class Command(BaseCommand):
    help = "Computes the results of the IPD."

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
            if answer.number_states() < 100:
                state_list = []
                nodes = []
                links = []
                for line in answer.automata.strip().split("\n"):
                    state, transition = line.strip().split(":")
                    state = state.strip()
                    if state not in state_list:
                        state_list.append(state)
                    action, next_state_coop, next_state_def = transition.strip().split(
                        ","
                    )
                    action = action.strip()
                    next_state_coop = next_state_coop.strip()
                    next_state_def = next_state_def.strip()
                    if next_state_coop not in state_list:
                        state_list.append(next_state_coop)
                    if next_state_def not in state_list:
                        state_list.append(next_state_def)

                    nodes.append(
                        {
                            "id": state_list.index(state),
                            "name": action.strip(),
                            "init": str(state == answer.initial_state.strip()),
                        }
                    )
                    if next_state_coop == next_state_def:
                        links.append(
                            {
                                "id": len(links),
                                "source": state_list.index(state),
                                "target": state_list.index(next_state_coop),
                                "label": "CD",
                            }
                        )
                    else:
                        links.append(
                            {
                                "id": len(links),
                                "source": state_list.index(state),
                                "target": state_list.index(next_state_coop),
                                "label": "C",
                            }
                        )
                        links.append(
                            {
                                "id": len(links),
                                "source": state_list.index(state),
                                "target": state_list.index(next_state_def),
                                "label": "D",
                            }
                        )
                json_data = "{nodes: ["
                for node in nodes:
                    json_data += "{"
                    for key in node:
                        json_data += "{}: {}, ".format(key, self.format_json(node[key]))
                    json_data = json_data[:-2] + "}, "
                json_data = json_data[:-2] + "], edges: ["
                for link in links:
                    json_data += "{"
                    for key in link:
                        json_data += "{}: {}, ".format(key, self.format_json(link[key]))
                    json_data = json_data[:-2] + "}, "
                json_data = json_data[:-2] + "]}"
                answer.graph_json_data = json_data
                answer.save()

    @staticmethod
    def format_json(x):
        try:
            y = int(x)
            if y == x:
                return int(x)
            return x
        except ValueError:
            return '"' + str(x).strip() + '"'
