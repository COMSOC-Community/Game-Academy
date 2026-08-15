import io

import numpy as np
from django.core.management import call_command
from django.test import TestCase, SimpleTestCase

from core.tests.helpers import make_session, make_user, make_player
from simp_poker.management.commands.simppoker_computeresults import (
    expected_utility,
    compute_best_response,
    compute_global_best_response,
    get_optimal_strategy,
    get_score_against_opt,
)
from simp_poker.models import Answer, Result
from simp_poker.tests.helpers import make_poker_game


def _answer(**overrides):
    data = dict(
        prob_p1_king=1, prob_p1_queen=0.5, prob_p1_jack=0.25,
        prob_p2_king=1, prob_p2_queen=0.5, prob_p2_jack=0,
    )
    data.update(overrides)
    return Answer(**data)


class ExpectedUtilityTests(SimpleTestCase):
    def test_identical_strategies_have_zero_expected_utility(self):
        answer = _answer()
        self.assertEqual(expected_utility(answer, answer), 0)

    def test_antisymmetric(self):
        a = _answer()
        b = _answer(prob_p1_king=0, prob_p2_jack=1)
        self.assertAlmostEqual(expected_utility(a, b), -expected_utility(b, a))

    def test_score_against_optimum_of_the_optimal_strategy_is_zero(self):
        optimal = get_optimal_strategy()
        self.assertAlmostEqual(get_score_against_opt(optimal), 0, places=5)


class ComputeBestResponseTests(SimpleTestCase):
    def test_best_response_to_never_calling(self):
        answer = _answer(prob_p2_king=0, prob_p2_queen=0, prob_p1_king=1, prob_p1_jack=0)
        response = compute_best_response(answer)
        np.testing.assert_array_equal(response, np.array([1, 1, 1, 1, 0, 0]))

    def test_best_response_to_always_calling(self):
        answer = _answer(prob_p2_king=1, prob_p2_queen=1, prob_p1_king=1, prob_p1_jack=1)
        response = compute_best_response(answer)
        np.testing.assert_array_equal(response, np.array([1, 1, 0, 1, 1, 0]))


class ComputeGlobalBestResponseTests(SimpleTestCase):
    def test_aggregates_across_answers(self):
        answers = [
            _answer(prob_p2_king=0, prob_p2_queen=0, prob_p1_king=1, prob_p1_jack=0),
            _answer(prob_p2_king=0, prob_p2_queen=0, prob_p1_king=1, prob_p1_jack=0),
        ]
        response = compute_global_best_response(answers)
        np.testing.assert_array_equal(response, np.array([1, 1, 1, 1, 0, 0]))


class SimppokerComputeResultsCommandTests(TestCase):
    def setUp(self):
        self.session = make_session("spcmdsession")
        self.game = make_poker_game(self.session)

    def run_command(self, **kwargs):
        stderr = io.StringIO()
        stdout = io.StringIO()
        call_command("simppoker_computeresults", stderr=stderr, stdout=stdout, **kwargs)
        return stdout.getvalue(), stderr.getvalue()

    def make_answer(self, name, **overrides):
        user = make_user(name)
        player = make_player(self.session, user, name=name)
        data = dict(
            game=self.game, player=player,
            prob_p1_king=1, prob_p1_queen=0.5, prob_p1_jack=0.25,
            prob_p2_king=1, prob_p2_queen=0.5, prob_p2_jack=0,
            motivation="m",
        )
        data.update(overrides)
        return Answer.objects.create(**data)

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

    def test_no_answers_creates_no_result(self):
        self.run_command(session=self.session.url_tag, game=self.game.url_tag)
        self.assertFalse(Result.objects.filter(game=self.game).exists())

    def test_round_robin_scores_are_zero_sum(self):
        self.make_answer("spcmdp1", prob_p1_king=1, prob_p1_queen=1, prob_p1_jack=1)
        self.make_answer("spcmdp2", prob_p1_king=0, prob_p1_queen=0, prob_p1_jack=0)
        self.make_answer("spcmdp3", prob_p2_king=0, prob_p2_queen=0, prob_p2_jack=0)
        self.run_command(session=self.session.url_tag, game=self.game.url_tag)
        total = sum(
            a.round_robin_score for a in Answer.objects.filter(game=self.game)
        )
        self.assertAlmostEqual(total, 0, places=5)

    def test_round_robin_positions_are_ranked(self):
        self.make_answer("spcmdp4", prob_p1_king=1, prob_p1_queen=1, prob_p1_jack=1)
        self.make_answer("spcmdp5", prob_p1_king=0, prob_p1_queen=0, prob_p1_jack=0)
        self.run_command(session=self.session.url_tag, game=self.game.url_tag)
        positions = sorted(
            a.round_robin_position for a in Answer.objects.filter(game=self.game)
        )
        self.assertEqual(positions, [1, 2])

    def test_winner_against_optimum_flag_matches_score_sign(self):
        self.make_answer("spcmdp6")
        self.run_command(session=self.session.url_tag, game=self.game.url_tag)
        answer = Answer.objects.get(player__name="spcmdp6")
        self.assertEqual(answer.winner_against_optimum, answer.score_against_optimum >= 0)

    def test_result_is_created_with_global_best_response(self):
        self.make_answer("spcmdp7")
        self.make_answer("spcmdp8")
        self.run_command(session=self.session.url_tag, game=self.game.url_tag)
        result = Result.objects.get(game=self.game)
        self.assertIsNotNone(result.global_best_response)
        self.assertEqual(len(result.global_best_response.split(",")), 6)

    def test_rerun_updates_existing_result_without_duplicating(self):
        self.make_answer("spcmdp9")
        self.run_command(session=self.session.url_tag, game=self.game.url_tag)
        self.make_answer("spcmdp10")
        self.run_command(session=self.session.url_tag, game=self.game.url_tag)
        self.assertEqual(Result.objects.filter(game=self.game).count(), 1)

    def test_best_response_is_stored_as_comma_separated_string(self):
        self.make_answer("spcmdp11")
        self.run_command(session=self.session.url_tag, game=self.game.url_tag)
        answer = Answer.objects.get(player__name="spcmdp11")
        self.assertEqual(len(answer.best_response.split(",")), 6)
