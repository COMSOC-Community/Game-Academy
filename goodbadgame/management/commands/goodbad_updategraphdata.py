from django.core.management.base import BaseCommand

from core.models import Session
from goodbadgame.models import *


class Command(BaseCommand):
    help = "Updates the JavaScript data for the graph of the good/bad game"

    def add_arguments(self, parser):
        parser.add_argument("--session", type=str, required=True)
        parser.add_argument("--game", type=str, required=True)
        parser.add_argument('--player', type=str, required=True)

    def handle(self, *args, **options):
        if not options["session"]:
            self.stderr.write(
                "ERROR: you need to give the URL tag of a session with the --session argument"
            )
            return
        session = Session.objects.filter(url_tag=options["session"])
        if not session.exists():
            self.stderr.write(
                "ERROR: no session with URL tag {} has been found".format(
                    options["session"]
                )
            )
            return
        session = session.first()

        if not options["game"]:
            self.stderr.write(
                "ERROR: you need to give the URL tag of a game with the --game argument"
            )
            return
        game = Game.objects.filter(
            session=session, url_tag=options["game"], game_type=NAME
        )
        if not game.exists():
            self.stderr.write(
                "ERROR: no game with URL tag {} has been found".format(options["game"])
            )
            return
        game = game.first()

        player = Player.objects.filter(name=options['player'], session=session)
        if not player.exists():
            print('ERROR: no player with name {} has been found'.format(options['player']))
            return
        player = player.first()

        print("Updating overall accuracy graph")
        if not game.goodbad_result.accuracy_js_data:
            new_js_data_graph = ''
            old_avg_acc = 0
        else:
            new_js_data_graph = game.goodbad_result.accuracy_js_data
            old_avg_acc = game.goodbad_result.crowd_accuracy
        player_answers = player.goodbad_answer.question_answers
        player_num_correct = player_answers.filter(is_correct=True)
        player_num_wrong = player_answers.filter(is_correct=False)
        player_num_ans = player_num_correct + player_num_wrong
        if player_num_ans > 0:
            new_avg_acc = old_avg_acc + 100 * player_num_correct / player_num_ans
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
