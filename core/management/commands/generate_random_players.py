from django.core.management.base import BaseCommand

from core.models import Session
from core.random import create_random_players


class Command(BaseCommand):
    help = "Populate players at random for a given session"

    def add_arguments(self, parser):
        parser.add_argument("n", type=int)
        parser.add_argument(
            "--session", type=str, required=True, help="Session URL tag"
        )

    def handle(self, *args, **options):
        if not options["session"]:
            self.stderr.write(
                "ERROR: you need to give the URL tag of a session with the --session argument"
            )
            return
        session = Session.objects.filter(url_tag=options["session"]).first()
        if not session:
            self.stderr.write(
                "ERROR: no session with URL tag {} has been found".format(
                    options["session"]
                )
            )
            return

        num_players = options["n"]
        if num_players <= 0:
            self.stderr.write(
                "The number of random answers to generate has to be at least 1."
            )
            return

        players = create_random_players(session, num_players)

        self.stdout.write(
            self.style.SUCCESS(
                f"{len(players)} players populated for session {session.name}."
            )
        )
