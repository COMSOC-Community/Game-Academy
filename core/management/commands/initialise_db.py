from django.core.management.base import BaseCommand

from core.constants import TEAM_USER_USERNAME, TEAM_USER_PASSWORD
from core.models import CustomUser


class Command(BaseCommand):
    help = "Initialise the database with all the required objects."

    def handle(self, *args, **options):
        if CustomUser.objects.filter(username=TEAM_USER_USERNAME).exists():
            team_user = CustomUser.objects.create_user(
                username=TEAM_USER_USERNAME,
                password=TEAM_USER_PASSWORD,
                is_player=True,
                is_guest_player=True,
                is_team_player=True,
            )
            team_user.is_active = False
            team_user.save()
