import csv

from goodbadgame.models import Answer, Setting


def answers_to_csv(writer, game):
    writer = csv.writer(writer)
    writer.writerow(
        [
            "player_name",
            "is_team_player",
            "question_title",
            "selected_alt",
            "is_correct",
            "submission_time"
        ]
    )
    for answer in Answer.objects.filter(game=game):
        for q in answer.questions.all():
            row = [
                answer.player.name,
                answer.player.is_team_player,
                q.title
            ]
            question_answer = answer.question_answers.filter(question=q).first()
            if question_answer is not None:
                row.append(question_answer.selected_alt)
                row.append(question_answer.is_correct)
                row.append(question_answer.submission_time)
            else:
                row.append(None)
                row.append(None)
                row.append(None)
            writer.writerow(row)


def settings_to_csv(writer, game):
    setting = None
    try:
        setting = game.goodbad_setting
    except Setting.DoesNotExist:
        pass
    if setting:
        writer = csv.writer(writer)
        questions = setting.questions.all()
        writer.writerow(
            ["num_displayed_questions"] + [f"question_{k}" for k in range(questions.count())]
        )
        writer.writerow(
            [setting.num_displayed_questions] + [q.title for q in questions]
        )
