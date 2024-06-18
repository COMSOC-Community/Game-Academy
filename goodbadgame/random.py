import random

from goodbadgame.models import Answer, QuestionAnswer


def assign_random_questions(game, player_answer):
    pks = list(game.goodbad_setting.questions.values_list("pk", flat=True))
    pks = random.sample(
        pks,
        min(
            game.goodbad_setting.questions.count(),
            game.goodbad_setting.num_displayed_questions,
        ),
    )
    player_answer.questions.add(*game.goodbad_setting.questions.filter(pk__in=pks))
    player_answer.save()


def create_random_answers(game, players):
    answers = []
    for player in players:
        answers.append(Answer(game=game, player=player))
    answers = Answer.objects.bulk_create(answers)

    question_answers = []
    for player_answer in answers:
        assign_random_questions(game, player_answer)

        for question in player_answer.questions.all():
            selected_alt = (
                question.correct_alt
                if random.random() > 0.45
                else random.choice(question.alternatives.all())
            )
            question_answers.append(
                QuestionAnswer(
                    answer=player_answer,
                    question=question,
                    selected_alt=selected_alt,
                    is_correct=selected_alt == question.correct_alt,
                )
            )
    QuestionAnswer.objects.bulk_create(question_answers)
    return answers
