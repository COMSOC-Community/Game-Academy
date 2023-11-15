import random

from django.core.management.base import BaseCommand
from django.utils.crypto import get_random_string

from core.constants import player_username, guest_username
from core.models import Session, Player, CustomUser


class Command(BaseCommand):
    help = 'Populate players at random for a given session'

    def add_arguments(self, parser):
        parser.add_argument('session_url_tag', type=str, help='Session URL tag')
        parser.add_argument('num_players', type=int, help='Number of players to add')

    def handle(self, *args, **options):
        session_url_tag = options['session_url_tag']
        num_players = options['num_players']

        try:
            session = Session.objects.get(url_tag=session_url_tag)
        except Session.DoesNotExist:
            self.stdout.write(self.style.ERROR(f'Session with URL tag {session_url_tag} does not exist.'))
            return

        # Ensure the number of players is positive
        num_players = max(0, num_players)

        # Generate and populate players
        num_created = 0
        for _ in range(num_players):
            player_name = get_random_string(3).lower()
            while Player.objects.filter(name=player_name).exists():
                player_name = get_random_string(3).lower()
            guest = False
            if not session.need_registration:
                guest = random.random() > 0.5
            if guest:
                username = guest_username(session, player_name)
            else:
                username = player_username(session, player_name)
            password = player_name * 3
            user = CustomUser.objects.create_user(username=username, password=password, is_player=True)
            Player.objects.create(user=user, name=player_name, session=session, is_guest=guest)
            num_created += 1

        self.stdout.write(self.style.SUCCESS(f'{num_created} players populated for session {session_url_tag}.'))
