from django.core.management.base import BaseCommand


class Command(BaseCommand):
    help = "Initializes the database, to be run once when the server is set up."

    def handle(self, *args, **options):
        pass
