from django.core.management.base import BaseCommand

from auctiongame.models import Answer, Result
from core.models import Session, Game

from auctiongame.apps import AUCT_NAME


class Command(BaseCommand):
    help = 'Updates the values required for the results page, to be run each time a new answer is submitted.'

    def add_arguments(self, parser):
        parser.add_argument('--session', type=str, required=True)
        parser.add_argument('--game', type=str, required=True)

    def handle(self, *args, **options):
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
        game = Game.objects.filter(session=session, url_tag=options['game'], game_type=AUCT_NAME)
        if not game.exists():
            print('ERROR: no game with URL tag {} has been found'.format(options['game']))
            return
        game = game.first()

        try:
            game.result_auct
        except Result.DoesNotExist:
            result = Result.objects.create(
                game=game,
                histo_auct1_js_data="",
                histo_auct2_js_data="",
                histo_auct3_js_data="",
                histo_auct4_js_data="",
                histo_auct5_js_data="",
            )
            game.result_auct = result
            game.save()
