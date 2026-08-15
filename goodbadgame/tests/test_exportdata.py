import csv
import io

from django.test import TestCase

from core.tests.helpers import make_session, make_user, make_player
from goodbadgame.exportdata import answers_to_csv, settings_to_csv
from goodbadgame.models import Answer, QuestionAnswer, Setting
from goodbadgame.tests.helpers import make_goodbad_game, make_question


class AnswersToCsvTests(TestCase):
    def setUp(self):
        self.session = make_session("gdbdexportsession")
        self.game = make_goodbad_game(self.session)
        self.user = make_user("gdbdexportplayer")
        self.player = make_player(self.session, self.user)
        self.question = make_question("gdbdexportq")

    def test_header_row(self):
        buffer = io.StringIO()
        answers_to_csv(buffer, self.game)
        rows = list(csv.reader(io.StringIO(buffer.getvalue())))
        self.assertEqual(
            rows[0],
            ["player_name", "is_team_player", "question_title", "selected_alt", "is_correct",
             "submission_time"],
        )

    def test_row_for_answered_question(self):
        answer = Answer.objects.create(game=self.game, player=self.player)
        answer.questions.add(self.question)
        QuestionAnswer.objects.create(
            answer=answer, question=self.question, selected_alt=self.question.correct_alt,
            is_correct=True,
        )
        buffer = io.StringIO()
        answers_to_csv(buffer, self.game)
        rows = list(csv.reader(io.StringIO(buffer.getvalue())))
        self.assertEqual(rows[1][0], self.player.name)
        self.assertEqual(rows[1][2], self.question.title)
        self.assertEqual(rows[1][3], str(self.question.correct_alt))
        self.assertEqual(rows[1][4], "True")

    def test_row_for_unanswered_assigned_question_has_blanks(self):
        answer = Answer.objects.create(game=self.game, player=self.player)
        answer.questions.add(self.question)
        buffer = io.StringIO()
        answers_to_csv(buffer, self.game)
        rows = list(csv.reader(io.StringIO(buffer.getvalue())))
        self.assertEqual(rows[1][3], "")
        self.assertEqual(rows[1][4], "")


class SettingsToCsvTests(TestCase):
    def setUp(self):
        self.session = make_session("gdbdexportsettingsession")
        self.game = make_goodbad_game(self.session)

    def test_no_setting_produces_empty_output(self):
        buffer = io.StringIO()
        settings_to_csv(buffer, self.game)
        self.assertEqual(buffer.getvalue(), "")

    def test_setting_row_lists_all_questions(self):
        q1 = make_question("gdbdexportsettingq1")
        q2 = make_question("gdbdexportsettingq2")
        setting = Setting.objects.create(game=self.game, num_displayed_questions=3)
        buffer = io.StringIO()
        settings_to_csv(buffer, self.game)
        rows = list(csv.reader(io.StringIO(buffer.getvalue())))
        self.assertEqual(rows[0][0], "num_displayed_questions")
        self.assertEqual(rows[1][0], "3")
        self.assertEqual(set(rows[1][1:]), {q1.title, q2.title})
