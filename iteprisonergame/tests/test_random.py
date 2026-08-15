from django.test import TestCase

from core.tests.helpers import make_session, make_user, make_player
from iteprisonergame.models import Answer
from iteprisonergame.random import create_random_answers
from iteprisonergame.tests.helpers import make_itepris_game


class CreateRandomAnswersTests(TestCase):
    def setUp(self):
        self.session = make_session("ipdrandomsession")
        self.game = make_itepris_game(self.session)
        self.players = [
            make_player(self.session, make_user(f"ipdrandomplayer{i}"))
            for i in range(3)
        ]

    def test_creates_one_answer_per_player(self):
        create_random_answers(self.game, self.players)
        self.assertEqual(Answer.objects.filter(game=self.game).count(), 3)

    def test_generated_automata_is_well_formed(self):
        from iteprisonergame.automata import MooreMachine

        create_random_answers(self.game, self.players)
        for answer in Answer.objects.filter(game=self.game):
            machine = MooreMachine()
            machine.initial_state = answer.initial_state
            errors = machine.parse(answer.automata.strip().split("\n"))
            self.assertEqual(errors, [])
            self.assertEqual(machine.test_validity(["C", "D"]), [])

    def test_initial_state_is_zero(self):
        create_random_answers(self.game, self.players)
        for answer in Answer.objects.filter(game=self.game):
            self.assertEqual(answer.initial_state, "0")

    def test_name_has_five_characters(self):
        create_random_answers(self.game, self.players)
        for answer in Answer.objects.filter(game=self.game):
            self.assertEqual(len(answer.name), 5)

    def test_no_players_creates_no_answers(self):
        answers = create_random_answers(self.game, [])
        self.assertEqual(answers, [])
