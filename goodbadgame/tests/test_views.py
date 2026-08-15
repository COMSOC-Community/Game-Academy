from django.test import TestCase
from django.urls import reverse

from core.tests.helpers import make_session, make_user, make_player
from goodbadgame.models import Answer, QuestionAnswer, Result, Setting
from goodbadgame.tests.helpers import make_goodbad_game, make_question


class GoodBadGameViewTestsBase(TestCase):
    def setUp(self):
        self.session = make_session("gdbdviewsession", visible=True)
        self.game = make_goodbad_game(self.session, visible=True, playable=True)
        self.questions = [make_question(f"gdbdviewq{i}") for i in range(3)]
        Setting.objects.create(game=self.game, num_displayed_questions=3)
        self.user = make_user("gdbdviewplayer")
        self.player = make_player(self.session, self.user)

    def index_url(self):
        return reverse("goodbad_game:index", args=(self.session.url_tag, self.game.url_tag))

    def submit_url(self):
        return reverse(
            "goodbad_game:submit_answer", args=(self.session.url_tag, self.game.url_tag)
        )

    def player_results_url(self):
        return reverse("goodbad_game:results", args=(self.session.url_tag, self.game.url_tag))

    def global_results_url(self):
        return reverse(
            "goodbad_game:global_results", args=(self.session.url_tag, self.game.url_tag)
        )


class IndexViewTests(GoodBadGameViewTestsBase):
    def test_get_renders_before_any_answer(self):
        self.client.login(username="gdbdviewplayer", password="pw")
        response = self.client.get(self.index_url())
        self.assertEqual(response.status_code, 200)

    def test_nav_answer_link_shown_when_answer_pending(self):
        Answer.objects.create(game=self.game, player=self.player)
        self.client.login(username="gdbdviewplayer", password="pw")
        response = self.client.get(self.index_url())
        self.assertTrue(response.context["game_nav_display_answer"])


class SubmitAnswerViewGetTests(GoodBadGameViewTestsBase):
    def test_first_visit_creates_answer_with_assigned_questions(self):
        self.client.login(username="gdbdviewplayer", password="pw")
        response = self.client.get(self.submit_url())
        self.assertEqual(response.status_code, 200)
        answer = Answer.objects.get(game=self.game, player=self.player)
        self.assertEqual(answer.questions.count(), 3)
        self.assertEqual(len(response.context["questions"]), 3)

    def test_second_visit_does_not_create_a_second_answer(self):
        self.client.login(username="gdbdviewplayer", password="pw")
        self.client.get(self.submit_url())
        self.client.get(self.submit_url())
        self.assertEqual(Answer.objects.filter(game=self.game, player=self.player).count(), 1)

    def test_no_questions_once_already_answered(self):
        answer = Answer.objects.create(game=self.game, player=self.player)
        answer.questions.add(self.questions[0])
        QuestionAnswer.objects.create(
            answer=answer, question=self.questions[0],
            selected_alt=self.questions[0].correct_alt, is_correct=True,
        )
        self.client.login(username="gdbdviewplayer", password="pw")
        response = self.client.get(self.submit_url())
        self.assertEqual(response.status_code, 200)
        self.assertNotIn("questions", response.context)

    def test_non_playable_game_blocks_non_admin(self):
        self.game.playable = False
        self.game.save()
        self.client.login(username="gdbdviewplayer", password="pw")
        response = self.client.get(self.submit_url())
        self.assertEqual(response.status_code, 404)


class SubmitAnswerViewPostTests(GoodBadGameViewTestsBase):
    def test_valid_submission_creates_question_answers(self):
        answer = Answer.objects.create(game=self.game, player=self.player)
        answer.questions.add(*self.questions)
        self.client.login(username="gdbdviewplayer", password="pw")
        post_data = {
            f"{q.slug}_selector": str(q.correct_alt.pk) for q in self.questions
        }
        response = self.client.post(self.submit_url(), post_data)
        self.assertEqual(response.status_code, 200)
        self.assertEqual(QuestionAnswer.objects.filter(answer=answer).count(), 3)
        self.assertTrue(
            QuestionAnswer.objects.filter(answer=answer, is_correct=True).count() == 3
        )
        self.assertTrue(response.context["submitted_answer"])

    def test_wrong_alternative_is_recorded_as_incorrect(self):
        answer = Answer.objects.create(game=self.game, player=self.player)
        answer.questions.add(self.questions[0])
        wrong_alt = self.questions[0].alternatives.exclude(
            pk=self.questions[0].correct_alt.pk
        ).first()
        self.client.login(username="gdbdviewplayer", password="pw")
        response = self.client.post(
            self.submit_url(), {f"{self.questions[0].slug}_selector": str(wrong_alt.pk)}
        )
        self.assertEqual(response.status_code, 200)
        qa = QuestionAnswer.objects.get(answer=answer, question=self.questions[0])
        self.assertFalse(qa.is_correct)

    def test_unanswered_questions_get_no_question_answer(self):
        answer = Answer.objects.create(game=self.game, player=self.player)
        answer.questions.add(*self.questions)
        self.client.login(username="gdbdviewplayer", password="pw")
        response = self.client.post(
            self.submit_url(),
            {f"{self.questions[0].slug}_selector": str(self.questions[0].correct_alt.pk)},
        )
        self.assertEqual(response.status_code, 200)
        self.assertEqual(QuestionAnswer.objects.filter(answer=answer).count(), 1)

    def test_management_command_runs_when_flag_enabled(self):
        self.game.run_management_after_submit = True
        self.game.save()
        answer = Answer.objects.create(game=self.game, player=self.player)
        answer.questions.add(*self.questions)
        self.client.login(username="gdbdviewplayer", password="pw")
        post_data = {
            f"{q.slug}_selector": str(q.correct_alt.pk) for q in self.questions
        }
        self.client.post(self.submit_url(), post_data)
        self.assertTrue(Result.objects.filter(game=self.game).exists())


class GlobalResultsViewTests(GoodBadGameViewTestsBase):
    def test_hidden_results_block_non_admin(self):
        self.game.results_visible = False
        self.game.save()
        self.client.login(username="gdbdviewplayer", password="pw")
        response = self.client.get(self.global_results_url())
        self.assertEqual(response.status_code, 404)

    def test_no_result_yet_renders_without_crash(self):
        self.game.results_visible = True
        self.game.save()
        self.client.login(username="gdbdviewplayer", password="pw")
        response = self.client.get(self.global_results_url())
        self.assertEqual(response.status_code, 200)
        self.assertNotIn("global_results", response.context)

    def test_result_present_with_answers_shows_global_results(self):
        self.game.results_visible = True
        self.game.save()
        answer = Answer.objects.create(game=self.game, player=self.player)
        answer.questions.add(*self.questions)
        Result.objects.create(game=self.game)
        self.client.login(username="gdbdviewplayer", password="pw")
        response = self.client.get(self.global_results_url())
        self.assertEqual(response.status_code, 200)
        self.assertTrue(response.context["global_results"])
        self.assertEqual(len(response.context["questions_answer_result"]), 3)


class PlayerResultsViewTests(GoodBadGameViewTestsBase):
    def test_hidden_results_block_non_admin(self):
        self.game.results_visible = False
        self.game.save()
        self.client.login(username="gdbdviewplayer", password="pw")
        response = self.client.get(self.player_results_url())
        self.assertEqual(response.status_code, 404)

    def test_no_result_yet_renders_without_crash(self):
        self.game.results_visible = True
        self.game.save()
        self.client.login(username="gdbdviewplayer", password="pw")
        response = self.client.get(self.player_results_url())
        self.assertEqual(response.status_code, 200)
        self.assertNotIn("game_result", response.context)

    def test_result_present_shows_player_question_details(self):
        self.game.results_visible = True
        self.game.save()
        answer = Answer.objects.create(game=self.game, player=self.player, score=1, accuracy=1.0)
        answer.questions.add(self.questions[0])
        QuestionAnswer.objects.create(
            answer=answer, question=self.questions[0],
            selected_alt=self.questions[0].correct_alt, is_correct=True,
        )
        Result.objects.create(game=self.game)
        self.client.login(username="gdbdviewplayer", password="pw")
        response = self.client.get(self.player_results_url())
        self.assertEqual(response.status_code, 200)
        self.assertEqual(len(response.context["questions_answer_result"]), 1)
