from django.db import IntegrityError
from django.test import TestCase

from core.tests.helpers import make_session, make_user, make_player
from goodbadgame.models import Alternative, Answer, Question, QuestionAnswer, QuestionResult, Result, Setting
from goodbadgame.tests.helpers import make_goodbad_game, make_question


class AlternativeModelTests(TestCase):
    def test_str_returns_slug(self):
        alt = Alternative.objects.create(slug="myalt", text="Some text")
        self.assertEqual(str(alt), "myalt")

    def test_slug_must_be_unique(self):
        Alternative.objects.create(slug="dupealt")
        with self.assertRaises(IntegrityError):
            Alternative.objects.create(slug="dupealt")


class QuestionModelTests(TestCase):
    def test_str_returns_title(self):
        question = make_question("qstr")
        self.assertEqual(str(question), "qstr")

    def test_random_order_alternatives_returns_all_alternatives(self):
        question = make_question("qorder", num_alts=4)
        ordered = question.random_order_alternatives()
        self.assertEqual(set(ordered), set(question.alternatives.all()))
        self.assertEqual(len(ordered), 4)


class SettingModelTests(TestCase):
    def setUp(self):
        self.session = make_session("gdbdsettingsession")
        self.game = make_goodbad_game(self.session)

    def test_default_num_displayed_questions(self):
        setting = Setting.objects.create(game=self.game)
        self.assertEqual(setting.num_displayed_questions, 10)

    def test_new_setting_auto_populates_with_all_existing_questions(self):
        q1 = make_question("gdbdautoq1")
        q2 = make_question("gdbdautoq2")
        setting = Setting.objects.create(game=self.game)
        self.assertEqual(set(setting.questions.all()), {q1, q2})

    def test_setting_created_with_explicit_questions_is_not_overridden(self):
        q1 = make_question("gdbdexpq1")
        q2 = make_question("gdbdexpq2")
        setting = Setting.objects.create(game=self.game)
        setting.questions.set([q1])
        # Re-saving should not add q2 since questions is already non-empty.
        setting.save()
        self.assertEqual(set(setting.questions.all()), {q1})


class AnswerModelTests(TestCase):
    def setUp(self):
        self.session = make_session("gdbdanswersession")
        self.game = make_goodbad_game(self.session)
        self.user = make_user("gdbdanswerplayer")
        self.player = make_player(self.session, self.user)

    def test_str(self):
        answer = Answer.objects.create(game=self.game, player=self.player)
        self.assertIn(self.player.display_name(), str(answer))
        self.assertIn(self.game.name, str(answer))


class QuestionAnswerModelTests(TestCase):
    def setUp(self):
        self.session = make_session("gdbdqanswersession")
        self.game = make_goodbad_game(self.session)
        self.user = make_user("gdbdqanswerplayer")
        self.player = make_player(self.session, self.user)
        self.answer = Answer.objects.create(game=self.game, player=self.player)
        self.question = make_question("gdbdqastr")

    def test_str_correct(self):
        alt = self.question.correct_alt
        qa = QuestionAnswer.objects.create(
            answer=self.answer, question=self.question, selected_alt=alt, is_correct=True,
        )
        self.assertIn("Correct", str(qa))

    def test_str_wrong(self):
        wrong_alt = self.question.alternatives.exclude(pk=self.question.correct_alt.pk).first()
        qa = QuestionAnswer.objects.create(
            answer=self.answer, question=self.question, selected_alt=wrong_alt, is_correct=False,
        )
        self.assertIn("Wrong", str(qa))


class ResultModelTests(TestCase):
    def setUp(self):
        self.session = make_session("gdbdresultsession")
        self.game = make_goodbad_game(self.session)

    def test_one_to_one_with_game(self):
        result = Result.objects.create(game=self.game)
        self.assertEqual(self.game.goodbad_result, result)

    def test_str(self):
        result = Result.objects.create(game=self.game)
        self.assertIn(self.game.name, str(result))


class QuestionResultModelTests(TestCase):
    def setUp(self):
        self.session = make_session("gdbdqresultsession")
        self.game = make_goodbad_game(self.session)
        self.result = Result.objects.create(game=self.game)
        self.question = make_question("gdbdqresultq")

    def test_str(self):
        qr = QuestionResult.objects.create(result=self.result, question=self.question)
        self.assertIn(self.question.title, str(qr))

    def test_unique_together_result_question(self):
        QuestionResult.objects.create(result=self.result, question=self.question)
        with self.assertRaises(IntegrityError):
            QuestionResult.objects.create(result=self.result, question=self.question)
