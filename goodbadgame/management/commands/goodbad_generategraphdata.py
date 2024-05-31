from django.core.management.base import BaseCommand

import os

from goodbadgame.models import *


class Command(BaseCommand):
    help = "Generates the JavaScript data for the graph of the good bad game"

    def add_arguments(self, parser):
        parser.add_argument('--session', type=str, required=True)

    def handle(self, *args, **options):
        session = Session.objects.filter(slug=options['session'])
        if not session.exists():
            print('ERROR: no session with short name {} has been found'.format(options['session']))
            return
        session = session.first()

        print("Creating good/bad graphs")
        for question in session.questions.all():
            # Computing the accuracy
            answers = Answer.objects.filter(question=question, player__session=session)
            timestamps = answers.order_by('timestamp').values_list('timestamp', flat=True).distinct()
            accuracy_js_data = ''
            for timestamp in timestamps:
                tmp_answers = answers.filter(timestamp__lte=timestamp)
                score_correct = tmp_answers.filter(is_correct=True).count()
                score_wrong = tmp_answers.filter(is_correct=False).count()
                accuracy_js_data += "['{}', '{}'],\n".format(tmp_answers.count(),
                                                             100 * score_correct / (score_correct + score_wrong))
            JSGraphData.objects.update_or_create(
                question=question,
                session=session,
                defaults={
                    'data': accuracy_js_data
                }
            )

        print("Creating overall accuracy graph")
        # Creating the overall accuracy graph
        players = sorted(Player.objects.filter(session=session).exclude(answers=None),
                         key=lambda player: player.answers.first().timestamp)
        accuracy_js_data = ''
        avg_acc_js_data = ''
        for i in range(len(players)):
            player_answers = Answer.objects.filter(player__in=players[:i + 1])
            crowd_num_correct = 0
            crowd_num_wrong = 0
            for question in session.questions.all():
                question_answers = player_answers.filter(question=question)
                if question_answers.exists():
                    num_correct = question_answers.filter(is_correct=True).count()
                    num_wrong = question_answers.filter(is_correct=False).count()
                    if num_correct > num_wrong:
                        crowd_num_correct += 1
                    else:
                        crowd_num_wrong += 1
            if crowd_num_correct + crowd_num_wrong > 0:
                crowd_accuracy = 100 * crowd_num_correct / (crowd_num_correct + crowd_num_wrong)
            else:
                crowd_accuracy = 0
            avg_player_score = 0
            for player in players[:i + 1]:
                player_count = player.questions_count()
                avg_player_score += 100 * player_count[1] / sum(player_count)
            avg_player_score /= i + 1
            accuracy_js_data += "['{}', '{}', '{}'],\n".format(i + 1, crowd_accuracy, avg_player_score)
        session.accuracy_js_data = accuracy_js_data
        session.avg_acc_js_data = avg_acc_js_data
        session.save()

        print('All done, graph data are now saved')
