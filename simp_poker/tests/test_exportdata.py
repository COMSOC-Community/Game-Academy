import csv
import io

from django.test import TestCase

from core.tests.helpers import make_session, make_user, make_player
from simp_poker.exportdata import answers_to_csv
from simp_poker.models import Answer
from simp_poker.tests.helpers import make_poker_game


class AnswersToCsvTests(TestCase):
    def setUp(self):
        self.session = make_session("spexportsession")
        self.game = make_poker_game(self.session)
        self.user = make_user("spexportplayer")
        self.player = make_player(self.session, self.user)

    def test_header_row(self):
        buffer = io.StringIO()
        answers_to_csv(buffer, self.game)
        rows = list(csv.reader(io.StringIO(buffer.getvalue())))
        self.assertEqual(
            rows[0],
            [
                "player_name", "is_team_player", "prob_p1_king", "prob_p1_queen",
                "prob_p1_jack", "prob_p2_king", "prob_p2_queen", "prob_p2_jack",
                "motivation", "round_robin_score", "round_robin_position",
                "round_robin_with_opt_score", "round_robin_with_opt_position",
                "score_against_optimum", "winner_against_optimum", "best_response",
                "score_against_best_response", "submission_time",
            ],
        )

    def test_answer_row_content(self):
        Answer.objects.create(
            game=self.game, player=self.player,
            prob_p1_king=1, prob_p1_queen=0.5, prob_p1_jack=0.25,
            prob_p2_king=1, prob_p2_queen=0.5, prob_p2_jack=0,
            motivation="reasoning", round_robin_position=1, winner_against_optimum=True,
        )
        buffer = io.StringIO()
        answers_to_csv(buffer, self.game)
        rows = list(csv.reader(io.StringIO(buffer.getvalue())))
        self.assertEqual(rows[1][0], self.player.name)
        self.assertEqual(rows[1][2], "1.0")
        self.assertEqual(rows[1][8], "reasoning")
        self.assertEqual(rows[1][10], "1")
        self.assertEqual(rows[1][14], "True")

    def test_only_this_games_answers_are_included(self):
        other_game = make_poker_game(self.session, url_tag="pokr2", name="Poker2")
        Answer.objects.create(
            game=other_game, player=self.player,
            prob_p1_king=1, prob_p1_queen=1, prob_p1_jack=1,
            prob_p2_king=1, prob_p2_queen=1, prob_p2_jack=1,
            motivation="other game",
        )
        buffer = io.StringIO()
        answers_to_csv(buffer, self.game)
        rows = list(csv.reader(io.StringIO(buffer.getvalue())))
        self.assertEqual(len(rows), 1)
