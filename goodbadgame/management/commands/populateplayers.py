from django.core.management.base import BaseCommand
from django.core import management

import random
import string

from goodbadgame.models import *


class Command(BaseCommand):
    help = 'Randomly populates the database with players and their answers'

    def add_arguments(self, parser):
        parser.add_argument('--session', type=str, required=True)
        parser.add_argument('-n', type=int)

    def handle(self, *args, **options):
        if not options['session']:
            print('ERROR: you need to give the short name of a sessions with the --session argument')
            return

        session = Session.objects.filter(slug=options['session'])
        if not session.exists():
            print('ERROR: no session with short name {} has been found'.format(options['session']))
            return
        session = session.first()

        num_players = 30
        if options['n']:
            num_players = int(options['n'])

        for i in range(num_players):
            name = ''.join(random.choice(string.ascii_lowercase) for i in range(10))
            while Player.objects.filter(name=name).exists():
                name = ''.join(random.choice(string.ascii_lowercase) for i in range(10))
            slug = name + "_"
            slug_index = 0
            while Player.objects.filter(slug=slug + str(slug_index)).exists():
                slug_index += 1
            player_obj = Player.objects.create(
                name=name,
                slug=slug + str(slug_index),
                session=session
            )
            pks = list(session.questions.values_list('pk', flat=True))
            pks = random.sample(pks, min(session.questions.count(), session.num_displayed_questions))
            player_obj.questions.add(*session.questions.filter(pk__in=pks))
            player_obj.save()
            for question in player_obj.questions.all():
                answer = question.correct_alt if random.random() > 0.3 else random.choice(question.alternatives.all())
                Answer.objects.create(
                    player=player_obj,
                    question=question,
                    answer=answer,
                    is_correct=answer == question.correct_alt
                )

        print("Done, generating the JS graph data")
        management.call_command("generatejsgraphdata", session=session.slug)
