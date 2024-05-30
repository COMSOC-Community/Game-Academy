from django.core.management.base import BaseCommand

from goodbadgame.models import *


class Command(BaseCommand):
    help = "Updates the JavaScript data for the graph of the good/bad game"

    def add_arguments(self, parser):
        parser.add_argument('--session', type=str, required=True)
        parser.add_argument('--player', type=str, required=True)

    def handle(self, *args, **options):
        session = Session.objects.filter(slug=options['session'])
        if not session.exists():
            print('ERROR: no session with short name {} has been found'.format(options['session']))
            return
        session = session.first()

        player = Player.objects.filter(name=options['player'], session=session)
        if not player.exists():
            print('ERROR: no player with name {} has been found'.format(options['player']))
            return
        player = player.first()

        print("Updating overall accuracy graph")
        if not session.accuracy_js_data:
            new_js_data_graph = ''
            old_avg_acc = 0
        else:
            new_js_data_graph = session.accuracy_js_data
            old_avg_acc = float(new_js_data_graph.splitlines()[-1].split(',')[2].strip()[1:-2])
            old_avg_acc *= Player.objects.filter(session=session).exclude(answers=None).count() - 1
        print(old_avg_acc)
        player_count = player.questions_count()
        if sum(player_count) > 0:
            new_avg_acc = old_avg_acc + 100 * (player_count[1] / sum(player_count))
        else:
            new_avg_acc = old_avg_acc
        num_players = Player.objects.filter(session=session).exclude(answers=None).count()
        if num_players > 0:
            new_avg_acc /= num_players
            print(new_avg_acc)
            session_global_count = session.questions_count()
            new_js_data_graph += "['{}', '{}', '{}'],\n".format(num_players,
                                                                100 * session_global_count[1] / sum(session_global_count),
                                                                new_avg_acc)
            session.accuracy_js_data = new_js_data_graph
            session.save()

            print("Updating good/bad graphs")
            for question in player.questions.all():
                player_answer = Answer.objects.filter(question=question, player=player)
                if player_answer.exists():
                    player_answer = player_answer.first()
                    js_data_graph_obj = question.js_graph_data.filter(session=session)
                    if js_data_graph_obj.exists():
                        js_data_graph_obj = js_data_graph_obj.first()
                        new_js_data_graph = js_data_graph_obj.data
                        question_count = question.crowd_count(session=session)

                        if sum(question_count) > 0:
                            new_js_data_graph += "['{}', '{}'],\n".format(sum(question_count),
                                                                          int(10000 * question_count[1] / sum(question_count)) / 100)
                            js_data_graph_obj.data = new_js_data_graph
                            js_data_graph_obj.save()
                    else:
                        JSGraphData.objects.create(
                            data="['{}', '{}'],\n".format(1, 100 if player_answer.is_correct else 0),
                            session=session,
                            question=question
                        )

        print('All done, graph data are now updated')
