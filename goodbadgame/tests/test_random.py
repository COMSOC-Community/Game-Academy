from django.test import TestCase

from core.tests.helpers import make_session, make_user, make_player
from goodbadgame.models import Answer, QuestionAnswer, Setting
from goodbadgame.random import assign_random_questions, create_random_answers
from goodbadgame.tests.helpers import make_goodbad_game, make_question


class AssignRandomQuestionsTests(TestCase):
    def setUp(self):
        self.session = make_session("gdbdassignrandomsession")
        self.game = make_goodbad_game(self.session)
        self.user = make_user("gdbdassignrandomplayer")
        self.player = make_player(self.session, self.user)
        self.questions = [make_question(f"gdbdassignq{i}") for i in range(5)]
        self.setting = Setting.objects.create(game=self.game, num_displayed_questions=3)

    def test_assigns_at_most_num_displayed_questions(self):
        answer = Answer.objects.create(game=self.game, player=self.player)
        assign_random_questions(self.game, answer)
        self.assertEqual(answer.questions.count(), 3)

    def test_assigns_all_questions_when_fewer_than_the_limit(self):
        self.setting.num_displayed_questions = 100
        self.setting.save()
        answer = Answer.objects.create(game=self.game, player=self.player)
        assign_random_questions(self.game, answer)
        self.assertEqual(answer.questions.count(), 5)

    def test_assigned_questions_are_a_subset_of_the_setting_questions(self):
        answer = Answer.objects.create(game=self.game, player=self.player)
        assign_random_questions(self.game, answer)
        assigned = set(answer.questions.all())
        self.assertTrue(assigned.issubset(set(self.setting.questions.all())))


class CreateRandomAnswersTests(TestCase):
    def setUp(self):
        self.session = make_session("gdbdrandomanswersession")
        self.game = make_goodbad_game(self.session)
        self.questions = [make_question(f"gdbdrandomanswerq{i}") for i in range(4)]
        Setting.objects.create(game=self.game, num_displayed_questions=4)
        self.players = [
            make_player(self.session, make_user(f"gdbdrandomanswerplayer{i}"))
            for i in range(3)
        ]

    def test_creates_one_answer_per_player(self):
        create_random_answers(self.game, self.players)
        self.assertEqual(Answer.objects.filter(game=self.game).count(), 3)

    def test_each_answer_gets_question_answers(self):
        create_random_answers(self.game, self.players)
        for answer in Answer.objects.filter(game=self.game):
            self.assertEqual(
                QuestionAnswer.objects.filter(answer=answer).count(), 4
            )

    def test_is_correct_matches_selected_alt(self):
        create_random_answers(self.game, self.players)
        for qa in QuestionAnswer.objects.filter(answer__game=self.game):
            self.assertEqual(qa.is_correct, qa.selected_alt == qa.question.correct_alt)

    def test_no_players_creates_no_answers(self):
        answers = create_random_answers(self.game, [])
        self.assertEqual(answers, [])
