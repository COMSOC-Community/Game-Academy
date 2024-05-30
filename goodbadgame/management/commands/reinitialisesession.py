from django.core.management.base import BaseCommand

from goodbadgame.models import *


class Command(BaseCommand):
    help = "Reinitialises a given session"

    def add_arguments(self, parser):
        parser.add_argument('--session', type=str, required=True)

    def handle(self, *args, **options):
        session = Session.objects.filter(slug=options['session'])
        if not session.exists():
            print('ERROR: no session with short name {} has been found'.format(options['session']))
            return
        session = session.first()

        session.accuracy_js_data = None
        session.save()

        Player.objects.filter(session=session).delete()
        JSGraphData.objects.filter(session=session).delete()

        print('Session (re)initialised')
