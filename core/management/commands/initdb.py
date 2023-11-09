from django.contrib.auth.models import Group
from django.core.management.base import BaseCommand

from core.constants import SESSION_MANAGER_GROUP, GUEST_PLAYER_GROUP, PLAYER_GROUP


class Command(BaseCommand):
    help = "Initializes the database, to be run once when the server is set up."

    def handle(self, *args, **options):
        pass
