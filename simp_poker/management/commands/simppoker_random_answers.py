import random

from django.core.management.base import BaseCommand

from core.constants import player_username, guest_username
from core.models import Session, Player, CustomUser, Game
from simp_poker.apps import NAME
from simp_poker.models import Answer


class Command(BaseCommand):
    help = "Randomly populates the answers of the simplified poker game."

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

        answers = [
            ['blank 1', 1, 0.5, 0.1, 1, 0.4, 0],
            ['blank 2', 1, 0.7, 0.2, 1, 0.5, 0],
            ['smiley', 1, 1, 0.33, 1, 1, 0],
            ['claimimng to be ulle', 1, 1, 0, 1, 0, 0],
            ['Aditya', 1, 0.8, 0.3, 0.5, 0.5, 0.5],
            ['Ana', 1, 1 / 2, 1 / 3, 1, 1 / 3, 0],
            ['Aniek', 1, 0.6, 0.2, 1, 0.2, 0],
            ['Andreas', 1, 1, 0.25, 1, 0.5, 0],
            ['Arend', 0.8, 0.6, 0.3, 1, 0.3, 0],
            ['Boaz', 1, 2 / 3, 1 / 3, 1, 2 / 3, 0],
            ['Brendan', 1, 0.7, 0.2, 1, 0.2, 0],
            ['Chrysa', 1, 1 / 2, 1 / 3, 1, 1 / 2, 0],
            ['Daan idB', 1, 1 / 2, 1 / 5, 1, 4 / 5, 0],
            ['Daan S', 1, 1, 0, 1, 0, 0],
            ['Didier', 1, 1, 0.35, 1, 0, 0],
            ['Elynn', 1, 1 / 2, 1 / 3, 1, 1 / 2, 0],
            ['Frank W', 1, 1, 1, 1, 0.5, 0],
            ['Gijs', 1, 0.5, 0.1, 1, 0, 0],
            ['Horia', 1, 1, 1 / 3, 1, 0.5, 0],
            ['Jacques', 1, 0.8, 0.2, 1, 0.6, 0],
            ['Jelke', 1, 1 / 2, 0, 1, 1 / 2, 0],
            ['Jesse', 1, 0, 1, 1, 1, 0],
            ['Job', 1, 1, 1 / 2, 1, 1, 0],
            ['Jochem', 1, 0.5, 0.2, 1, 0.3, 0],
            ['Joel', 0.4, 0.1, 0.5, 0.6, 0.3, 0.5],
            ['Lisa', 1, 1 / 2, 1 / 3, 1, 1 / 3, 0],
            ['Matteo', 1, 0.75, 0.25, 1, 0.5, 0],
            ['Meggie', 1, 1 / 2, 0, 1, 1 / 5, 0],
            ['Minke', 1, 0.5, 0.25, 1, 0.55, 0],
            ['Pieter', 1, 1 / 2, 1 / 2, 1, 1 / 4, 0],
            ['Pratik', 1, 1 / 2, 1 / 4, 1, 1 / 4, 0],
            ['Ruiting', 1, 1, 0.25, 1, 0.5, 0],
            ['Satchit', 1, 0.66, 0.33, 1, 0.66, 0],
            ['Simon', 1, 0.5, 0.5, 1, 0.66, 0],
            ['Slawek', 1, 1, 1, 1, 0, 0],
            ['Stefan', 1, 0.5, 0.5, 1, 0.75, 0],
            ['Tim', 1, 1 / 2, 1 / 4, 1, 1 / 2, 0],
            ['Tisja', 1, 1, 1 / 2, 1, 2 / 3, 0],
            ['Valentions', 1, 0.75, 0.5, 1, 0.5, 0.25],
        ]

        for a in answers:
            player_name = a[0]
            if not Player.objects.filter(name=player_name, session=session).exists():
                username = player_username(session, player_name)
                user = CustomUser.objects.create_user(
                    username=username, password='azeazeaze', is_player=True
                )
                player = Player.objects.create(
                    user=user, name=player_name, session=session, is_guest=False
                )
                Answer.objects.update_or_create(
                    player=player,
                    game=game,
                    defaults={
                        "prob_p1_king": a[1],
                        "prob_p1_queen": a[2],
                        "prob_p1_jack": a[3],
                        "prob_p2_king": a[4],
                        "prob_p2_queen": a[5],
                        "prob_p2_jack": a[6],
                        "motivation": "Test player"
                    }
                )
