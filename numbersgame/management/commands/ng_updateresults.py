from django.core.exceptions import ObjectDoesNotExist
from django.core.management.base import BaseCommand
from django.db.models import Avg

from core.models import Session, Game

from numbersgame.apps import NG_NAME
from numbersgame.models import Answer, Result


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
        game = Game.objects.filter(session=session, url_tag=options['game'], game_type=NG_NAME)
        if not game.exists():
            print('ERROR: no game with URL tag {} has been found'.format(options['game']))
            return
        game = game.first()

        try:
            game.result_ng
        except ObjectDoesNotExist:
            result = Result.objects.create(
                game=game,
                histo_js_data="",
                histo_bin_size=3,
            )
            game.result_ng = result
            game.save()

        answers = Answer.objects.filter(game=game, answer__isnull=False)

        categories = {i: 0 for i in range(0, 101, game.result_ng.histo_bin_size)}

        average = answers.aggregate(Avg('answer'))['answer__avg']
        corrected_average = 2/3 * average
        best_answers = []
        smallest_gap = 100
        for answer in answers:
            category = int(int(answer.answer) / game.result_ng.histo_bin_size) * game.result_ng.histo_bin_size
            categories[category] += 1

            gap = abs(answer.answer - corrected_average)
            if gap < smallest_gap:
                smallest_gap = gap
                best_answers = [answer]
            elif gap == smallest_gap:
                best_answers.append(answer)
            answer.gap = gap
            answer.winner = False
            answer.save()
        for winner in best_answers:
            winner.winner = True
            winner.save()
        game.result_ng.average = average
        game.result_ng.corrected_average = corrected_average

        game.result_ng.histo_js_data = "\n".join(
            ["['{}-{}', {}],".format(key, min(key + game.result_ng.histo_bin_size - 1, 100), val)
             for key, val in categories.items()])
        game.result_ng.save()
        game.save()

        print("The results for the Numbers Game {} have been updated.".format(game.name))
