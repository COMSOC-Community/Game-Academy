from django.core.management.base import BaseCommand

from core.models import Session, Game, Player
from goodbadgame.apps import NAME
from goodbadgame.models import Answer, Result, QuestionResult


class Command(BaseCommand):
    help = (
        "Updates the result data for the good/bad game based on the latest submission"
    )

    def add_arguments(self, parser):
        parser.add_argument("--session", type=str, required=True)
        parser.add_argument("--game", type=str, required=True)
        parser.add_argument("--player", type=str, required=True)

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

        # We create the result object if it does not exist.
        try:
            game_result = game.goodbad_result
        except Result.DoesNotExist:
            game_result = Result.objects.create(game=game)

        player = Player.objects.filter(name=options["player"], session=session)
        if not player.exists():
            self.stderr.write(
                "ERROR: no player with name {} has been found".format(options["player"])
            )
            return
        player = player.first()

        if not game_result.accuracy_js_data:
            old_avg_acc = 0
        else:
            old_avg_acc = game_result.average_accuracy

        # Answers of the player
        player_question_answers = player.goodbad_answer.get(game=game).question_answers
        player_num_correct = player_question_answers.filter(is_correct=True).count()
        player_num_wrong = player_question_answers.filter(is_correct=False).count()
        player_num_ans = player_num_correct + player_num_wrong
        if player_num_ans > 0:
            player_acc = player_num_correct / player_num_ans
            Answer.objects.update_or_create(
                game=game,
                player=player,
                defaults={"score": player_num_correct, "accuracy": player_acc},
            )

            # Updating average accuracy
            num_answers = (
                Answer.objects.filter(game=game).exclude(score__isnull=True).count()
            )
            new_avg_acc = old_avg_acc + (player_acc - old_avg_acc) / num_answers
            game_result.average_accuracy = new_avg_acc

            # Updating question result
            crowd_improvement = 0
            for question_answer in player_question_answers.all():
                question_result, _ = QuestionResult.objects.get_or_create(
                    result=game_result, question=question_answer.question
                )
                # If it is the first answer we initialise
                if question_result.graph_js_data is None:
                    if question_answer.is_correct:
                        question_result.graph_js_data = "['1', '1'],\n"
                        question_result.num_correct_answers = 1
                        question_result.num_wrong_answers = 0
                        question_result.accuracy = 1.0
                        crowd_improvement += 1
                    else:
                        question_result.graph_js_data = "['1', '0'],\n"
                        question_result.num_correct_answers = 0
                        question_result.num_wrong_answers = 1
                        question_result.accuracy = 0.0
                else:
                    question_num_correct = question_result.num_correct_answers
                    question_num_wrong = question_result.num_wrong_answers
                    if question_answer.is_correct:
                        if question_num_correct == question_num_wrong:
                            crowd_improvement += 1
                        question_num_correct += 1
                    else:
                        if question_num_correct == question_num_wrong + 1:
                            crowd_improvement -= 1
                        question_num_wrong += 1
                    question_result.num_correct_answers = question_num_correct
                    question_result.num_wrong_answers = question_num_wrong
                    question_num_answers = question_num_correct + question_num_wrong
                    question_accuracy = question_num_correct / question_num_answers
                    question_result.accuracy = question_accuracy
                    question_result.graph_js_data += (
                        f"['{question_num_answers}', " f"'{question_accuracy}'],\n"
                    )
                question_result.save()

            # Updating crowd accuracy
            if game_result.crowd_num_correct is None:
                game_num_correct = crowd_improvement
            else:
                game_num_correct = game_result.crowd_num_correct + crowd_improvement
            game_num_answers = QuestionResult.objects.filter(result=game_result).count()
            if game_result.accuracy_js_data is None:
                old_accuracy_js_data = ""
            else:
                old_accuracy_js_data = game_result.accuracy_js_data
            old_accuracy_js_data += (
                f"['{num_answers}', "
                f"'{game_num_correct / game_num_answers}', "
                f"'{new_avg_acc}'],\n"
            )
            game_result.accuracy_js_data = old_accuracy_js_data
            game_result.crowd_num_correct = game_num_correct
            game_result.crowd_accuracy = game_num_correct / game_num_answers
            game_result.save()
