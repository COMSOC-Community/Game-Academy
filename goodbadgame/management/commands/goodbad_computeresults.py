from collections import Counter, defaultdict

from django.core.management.base import BaseCommand

from core.models import Session, Game
from goodbadgame.apps import NAME
from goodbadgame.models import Question, QuestionResult, Result, Answer, QuestionAnswer


class Command(BaseCommand):

    help = "Updates the result data for the good/bad game based on the latest submission"

    def add_arguments(self, parser):
        parser.add_argument("--session", type=str, required=True)
        parser.add_argument("--game", type=str, required=True)

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

        # Results for each question
        QuestionResult.objects.filter(result=game_result).delete()
        for question in game.goodbad_setting.questions.all():
            answers = question.answers.filter(answer__game=game)
            if answers.exists():
                timestamps = answers.order_by('submission_time').values_list('submission_time', flat=True).distinct()
                graph_js_data = ''
                num_correct = 0
                num_wrong = 0
                accuracy = 0
                for timestamp in timestamps:
                    tmp_answers = answers.filter(submission_time__lte=timestamp)
                    num_correct = tmp_answers.filter(is_correct=True).count()
                    num_wrong = tmp_answers.filter(is_correct=False).count()
                    accuracy = num_correct / (num_correct + num_wrong)
                    graph_js_data += "['{}', '{}'],\n".format(tmp_answers.count(), accuracy)
                QuestionResult.objects.update_or_create(
                    result=game_result,
                    question=question,
                    defaults={
                        "num_correct_answers": num_correct,
                        "num_wrong_answers": num_wrong,
                        "accuracy": accuracy,
                        "graph_js_data": graph_js_data
                    }
                )

        # Creating the overall accuracy graph
        answers = sorted(Answer.objects.filter(game=game).exclude(question_answers=None),
                         key=lambda ans: ans.question_answers.first().submission_time)
        for answer in answers:
            question_answers = answer.question_answers.all()
            for question_answer in question_answers:
                if question_answer.selected_alt == question_answer.question.correct_alt:
                    question_answer.is_correct = True
                else:
                    question_answer.is_correct = False
            QuestionAnswer.objects.bulk_update(question_answers, ["is_correct"])
            answer.score = answer.question_answers.filter(is_correct=True).count()
            answer.accuracy = answer.score / answer.question_answers.count()
        Answer.objects.bulk_update(answers, ["score", "accuracy"])
        accuracy_js_data = ''
        current_answers = []
        questions_count = defaultdict(lambda: 0)
        crowd_num_correct = 0
        crowd_num_wrong = 0
        crowd_accuracy = 0
        total_accuracy = 0
        num_answers = 0
        for num_answers, new_answer in enumerate(answers):
            current_answers.append(new_answer)
            for question_answer in new_answer.question_answers.all():
                if question_answer.is_correct:
                    questions_count[question_answer.question] += 1
                else:
                    questions_count[question_answer.question] -= 1
            crowd_num_correct = 0
            crowd_num_wrong = 0
            for v in questions_count.values():
                if v > 0:
                    crowd_num_correct += 1
                else:
                    crowd_num_wrong += 1
            if crowd_num_correct + crowd_num_wrong > 0:
                crowd_accuracy = crowd_num_correct / (crowd_num_correct + crowd_num_wrong)
            else:
                crowd_accuracy = 0
            total_accuracy += new_answer.accuracy
            accuracy_js_data += "['{}', '{}', '{}'],\n".format(num_answers + 1, crowd_accuracy, total_accuracy / (num_answers + 1))

        game_result.accuracy_js_data = accuracy_js_data
        game_result.average_accuracy = total_accuracy / (num_answers + 1)
        game_result.crowd_num_correct = crowd_num_correct
        game_result.crowd_accuracy = crowd_accuracy
        game_result.save()
