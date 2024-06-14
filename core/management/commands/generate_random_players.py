import random

from django.core.management.base import BaseCommand

from core.constants import player_username, guest_username
from core.models import Session, Player, CustomUser
from core.random import random_players


class Command(BaseCommand):
    help = "Populate players at random for a given session"

    def add_arguments(self, parser):
        parser.add_argument("n", type=int)
        parser.add_argument("session_url_tag", type=str, help="Session URL tag")

    def handle(self, *args, **options):
        session_url_tag = options["session_url_tag"]
        try:
            session = Session.objects.get(url_tag=session_url_tag)
        except Session.DoesNotExist:
            self.stdout.write(
                self.style.ERROR(
                    f"Session with URL tag {session_url_tag} does not exist."
                )
            )
            return

        num_players = options['n']
        if num_players <= 0:
            self.stderr.write(
                "The number of random answers to generate has to be at least 1."
            )
            return

        players = random_players(session, num_players)

        self.stdout.write(
            self.style.SUCCESS(
                f"{len(players)} players populated for session {session_url_tag}."
            )
        )
