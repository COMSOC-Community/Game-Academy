import io

from django.core.management import call_command
from django.test import TestCase

from core.tests.helpers import make_session, make_user, make_player
from goodbadgame.models import Answer, QuestionAnswer, QuestionResult, Result, Setting
from goodbadgame.tests.helpers import make_goodbad_game, make_question


class GoodbadComputeResultsCommandTests(TestCase):
    def setUp(self):
        self.session = make_session("gdbdcomputecmdsession")
        self.game = make_goodbad_game(self.session)
        self.q1 = make_question("gdbdcomputeq1")
        self.q2 = make_question("gdbdcomputeq2")
        Setting.objects.create(game=self.game, num_displayed_questions=2)

    def run_command(self, **kwargs):
        stderr = io.StringIO()
        stdout = io.StringIO()
        call_command("goodbad_computeresults", stderr=stderr, stdout=stdout, **kwargs)
        return stdout.getvalue(), stderr.getvalue()

    def make_answer(self, name, q1_correct, q2_correct):
        user = make_user(name)
        player = make_player(self.session, user, name=name)
        answer = Answer.objects.create(game=self.game, player=player)
        answer.questions.add(self.q1, self.q2)
        wrong1 = self.q1.alternatives.exclude(pk=self.q1.correct_alt.pk).first()
        wrong2 = self.q2.alternatives.exclude(pk=self.q2.correct_alt.pk).first()
        QuestionAnswer.objects.create(
            answer=answer, question=self.q1,
            selected_alt=self.q1.correct_alt if q1_correct else wrong1,
            is_correct=q1_correct,
        )
        QuestionAnswer.objects.create(
            answer=answer, question=self.q2,
            selected_alt=self.q2.correct_alt if q2_correct else wrong2,
            is_correct=q2_correct,
        )
        return answer

    def test_missing_session_argument_reports_error(self):
        _, stderr = self.run_command(session="", game=self.game.url_tag)
        self.assertIn("session", stderr)

    def test_unknown_session_reports_error(self):
        _, stderr = self.run_command(session="doesnotexist", game=self.game.url_tag)
        self.assertIn("no session", stderr)

    def test_missing_game_argument_reports_error(self):
        _, stderr = self.run_command(session=self.session.url_tag, game="")
        self.assertIn("game", stderr)

    def test_unknown_game_reports_error(self):
        _, stderr = self.run_command(session=self.session.url_tag, game="doesnotexist")
        self.assertIn("no game", stderr)

    def test_no_answers_does_not_crash_and_creates_empty_result(self):
        self.run_command(session=self.session.url_tag, game=self.game.url_tag)
        result = Result.objects.get(game=self.game)
        self.assertEqual(result.average_accuracy, 0)

    def test_answer_with_no_question_answers_is_excluded(self):
        user = make_user("gdbdcomputeempty")
        player = make_player(self.session, user, name="gdbdcomputeempty")
        Answer.objects.create(game=self.game, player=player)
        self.run_command(session=self.session.url_tag, game=self.game.url_tag)
        result = Result.objects.get(game=self.game)
        self.assertEqual(result.average_accuracy, 0)

    def test_answer_score_and_accuracy_are_recomputed(self):
        answer = self.make_answer("gdbdcomputep1", q1_correct=True, q2_correct=False)
        self.run_command(session=self.session.url_tag, game=self.game.url_tag)
        answer.refresh_from_db()
        self.assertEqual(answer.score, 1)
        self.assertEqual(answer.accuracy, 0.5)

    def test_question_result_accuracy_reflects_all_answers(self):
        self.make_answer("gdbdcomputep2", q1_correct=True, q2_correct=True)
        self.make_answer("gdbdcomputep3", q1_correct=True, q2_correct=False)
        self.make_answer("gdbdcomputep4", q1_correct=False, q2_correct=False)
        self.run_command(session=self.session.url_tag, game=self.game.url_tag)
        result = Result.objects.get(game=self.game)
        q1_result = QuestionResult.objects.get(result=result, question=self.q1)
        q2_result = QuestionResult.objects.get(result=result, question=self.q2)
        self.assertEqual(q1_result.num_correct_answers, 2)
        self.assertEqual(q1_result.num_wrong_answers, 1)
        self.assertAlmostEqual(q1_result.accuracy, 2 / 3)
        self.assertEqual(q2_result.num_correct_answers, 1)
        self.assertEqual(q2_result.num_wrong_answers, 2)
        self.assertAlmostEqual(q2_result.accuracy, 1 / 3)

    def test_average_accuracy_is_the_mean_of_all_answers_own_accuracy(self):
        self.make_answer("gdbdcomputep5", q1_correct=True, q2_correct=True)   # 1.0
        self.make_answer("gdbdcomputep6", q1_correct=True, q2_correct=False)  # 0.5
        self.make_answer("gdbdcomputep7", q1_correct=False, q2_correct=False)  # 0.0
        self.run_command(session=self.session.url_tag, game=self.game.url_tag)
        result = Result.objects.get(game=self.game)
        self.assertAlmostEqual(result.average_accuracy, 0.5)

    def test_crowd_accuracy_reflects_majority_correctness_per_question(self):
        # Q1: 2/3 majority correct. Q2: 1/3 majority wrong. So crowd gets Q1 right, Q2 wrong.
        self.make_answer("gdbdcomputep8", q1_correct=True, q2_correct=True)
        self.make_answer("gdbdcomputep9", q1_correct=True, q2_correct=False)
        self.make_answer("gdbdcomputep10", q1_correct=False, q2_correct=False)
        self.run_command(session=self.session.url_tag, game=self.game.url_tag)
        result = Result.objects.get(game=self.game)
        self.assertEqual(result.crowd_num_correct, 1)
        self.assertAlmostEqual(result.crowd_accuracy, 0.5)

    def test_rerun_does_not_duplicate_question_results(self):
        self.make_answer("gdbdcomputep11", q1_correct=True, q2_correct=True)
        self.run_command(session=self.session.url_tag, game=self.game.url_tag)
        self.make_answer("gdbdcomputep12", q1_correct=False, q2_correct=False)
        self.run_command(session=self.session.url_tag, game=self.game.url_tag)
        result = Result.objects.get(game=self.game)
        self.assertEqual(QuestionResult.objects.filter(result=result).count(), 2)


class GoodbadUpdateResultsCommandTests(TestCase):
    def setUp(self):
        self.session = make_session("gdbdupdatecmdsession")
        self.game = make_goodbad_game(self.session)
        self.q1 = make_question("gdbdupdateq1")
        self.q2 = make_question("gdbdupdateq2")
        Setting.objects.create(game=self.game, num_displayed_questions=2)

    def run_command(self, **kwargs):
        stderr = io.StringIO()
        stdout = io.StringIO()
        call_command("goodbad_updateresults", stderr=stderr, stdout=stdout, **kwargs)
        return stdout.getvalue(), stderr.getvalue()

    def make_pending_answer(self, name, q1_correct, q2_correct):
        user = make_user(name)
        player = make_player(self.session, user, name=name)
        answer = Answer.objects.create(game=self.game, player=player)
        answer.questions.add(self.q1, self.q2)
        wrong1 = self.q1.alternatives.exclude(pk=self.q1.correct_alt.pk).first()
        wrong2 = self.q2.alternatives.exclude(pk=self.q2.correct_alt.pk).first()
        QuestionAnswer.objects.create(
            answer=answer, question=self.q1,
            selected_alt=self.q1.correct_alt if q1_correct else wrong1,
            is_correct=q1_correct,
        )
        QuestionAnswer.objects.create(
            answer=answer, question=self.q2,
            selected_alt=self.q2.correct_alt if q2_correct else wrong2,
            is_correct=q2_correct,
        )
        return player

    def test_missing_session_argument_reports_error(self):
        _, stderr = self.run_command(session="", game=self.game.url_tag, player="x")
        self.assertIn("session", stderr)

    def test_unknown_session_reports_error(self):
        _, stderr = self.run_command(session="doesnotexist", game=self.game.url_tag, player="x")
        self.assertIn("no session", stderr)

    def test_missing_game_argument_reports_error(self):
        _, stderr = self.run_command(session=self.session.url_tag, game="", player="x")
        self.assertIn("game", stderr)

    def test_unknown_game_reports_error(self):
        _, stderr = self.run_command(
            session=self.session.url_tag, game="doesnotexist", player="x"
        )
        self.assertIn("no game", stderr)

    def test_unknown_player_reports_error(self):
        _, stderr = self.run_command(
            session=self.session.url_tag, game=self.game.url_tag, player="doesnotexist"
        )
        self.assertIn("no player", stderr)

    def test_first_player_sets_score_and_accuracy(self):
        player = self.make_pending_answer("gdbdupdatep1", q1_correct=True, q2_correct=False)
        self.run_command(
            session=self.session.url_tag, game=self.game.url_tag, player=player.name
        )
        answer = Answer.objects.get(game=self.game, player=player)
        self.assertEqual(answer.score, 1)
        self.assertEqual(answer.accuracy, 0.5)

    def test_first_player_sets_result_average_accuracy(self):
        player = self.make_pending_answer("gdbdupdatep2", q1_correct=True, q2_correct=True)
        self.run_command(
            session=self.session.url_tag, game=self.game.url_tag, player=player.name
        )
        result = Result.objects.get(game=self.game)
        self.assertEqual(result.average_accuracy, 1.0)

    def test_second_player_updates_running_average(self):
        p1 = self.make_pending_answer("gdbdupdatep3", q1_correct=True, q2_correct=True)
        self.run_command(session=self.session.url_tag, game=self.game.url_tag, player=p1.name)
        p2 = self.make_pending_answer("gdbdupdatep4", q1_correct=False, q2_correct=False)
        self.run_command(session=self.session.url_tag, game=self.game.url_tag, player=p2.name)
        result = Result.objects.get(game=self.game)
        self.assertAlmostEqual(result.average_accuracy, 0.5)

    def test_question_result_accumulates_across_players(self):
        p1 = self.make_pending_answer("gdbdupdatep5", q1_correct=True, q2_correct=True)
        self.run_command(session=self.session.url_tag, game=self.game.url_tag, player=p1.name)
        p2 = self.make_pending_answer("gdbdupdatep6", q1_correct=True, q2_correct=False)
        self.run_command(session=self.session.url_tag, game=self.game.url_tag, player=p2.name)
        result = Result.objects.get(game=self.game)
        q1_result = QuestionResult.objects.get(result=result, question=self.q1)
        q2_result = QuestionResult.objects.get(result=result, question=self.q2)
        self.assertEqual(q1_result.num_correct_answers, 2)
        self.assertEqual(q1_result.num_wrong_answers, 0)
        self.assertEqual(q2_result.num_correct_answers, 1)
        self.assertEqual(q2_result.num_wrong_answers, 1)
