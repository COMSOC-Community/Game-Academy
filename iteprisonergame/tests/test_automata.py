from django.test import SimpleTestCase

from iteprisonergame.automata import MooreMachine, fight, format_json
from iteprisonergame.tests.helpers import ALWAYS_COOPERATE, ALWAYS_DEFECT, TIT_FOR_TAT


def build(lines, initial_state="0"):
    machine = MooreMachine()
    machine.initial_state = initial_state
    errors = machine.parse(lines.strip().split("\n"))
    return machine, errors


class ParseTests(SimpleTestCase):
    def test_valid_single_line_parses_with_no_errors(self):
        machine, errors = build(ALWAYS_COOPERATE)
        self.assertEqual(errors, [])
        self.assertEqual(machine.outcome["0"], "C")
        self.assertEqual(machine.transitions["0"], {"C": "0", "D": "0"})

    def test_valid_multiline_parses_with_no_errors(self):
        machine, errors = build(TIT_FOR_TAT)
        self.assertEqual(errors, [])
        self.assertEqual(machine.outcome, {"0": "C", "1": "D"})
        self.assertEqual(machine.transitions["0"], {"C": "0", "D": "1"})
        self.assertEqual(machine.transitions["1"], {"C": "0", "D": "1"})

    def test_malformed_line_is_reported(self):
        machine, errors = build("this is not a valid line")
        self.assertEqual(len(errors), 1)
        self.assertIn("not formatted correctly", errors[0])

    def test_redefining_a_state_is_reported(self):
        machine, errors = build("0: C, 0, 1\n0: D, 0, 1")
        self.assertEqual(len(errors), 1)
        self.assertIn("redefines state 0", errors[0])

    def test_referenced_but_undefined_state_has_empty_transitions(self):
        machine, errors = build(ALWAYS_COOPERATE.replace("0, 0", "0, 1"))
        self.assertEqual(errors, [])
        self.assertIn("1", machine.transitions)
        self.assertEqual(machine.transitions["1"], {})

    def test_extra_internal_whitespace_is_tolerated(self):
        # Leading/trailing whitespace on the whole line is stripped before matching, and extra
        # spaces after the colon and after each comma are tolerated too -- but no space is
        # allowed between the state name and its colon, nor before a comma.
        machine, errors = build("  0:   C,  0,  0  ")
        self.assertEqual(errors, [])
        self.assertEqual(machine.outcome["0"], "C")


class TestValidityTests(SimpleTestCase):
    def test_fully_defined_automata_has_no_errors(self):
        machine, _ = build(TIT_FOR_TAT)
        self.assertEqual(machine.test_validity(["C", "D"]), [])

    def test_state_referenced_but_never_defined_is_reported(self):
        # State "1" is referenced as a target from state "0" but never given its own line.
        machine, _ = build(ALWAYS_COOPERATE.replace("0, 0", "0, 1"))
        errors = machine.test_validity(["C", "D"])
        self.assertEqual(len(errors), 2)
        self.assertTrue(all("state 1" in e for e in errors))


class TestConnectivityTests(SimpleTestCase):
    def test_fully_connected_automata_returns_none(self):
        machine, _ = build(TIT_FOR_TAT)
        self.assertIsNone(machine.test_connectivity())

    def test_unreachable_state_is_reported(self):
        machine, _ = build("0: C, 0, 0\n1: D, 1, 1")
        error = machine.test_connectivity()
        self.assertIsNotNone(error)
        self.assertIn("1", error)


class IsIsomorphicTests(SimpleTestCase):
    def test_identical_automata_are_isomorphic(self):
        m1, _ = build(TIT_FOR_TAT)
        m2, _ = build(TIT_FOR_TAT)
        self.assertTrue(m1.is_isomorphic(m2))

    def test_renamed_states_are_isomorphic(self):
        m1, _ = build(TIT_FOR_TAT)
        m2, _ = build("a: C, a, b\nb: D, a, b", initial_state="a")
        self.assertTrue(m1.is_isomorphic(m2))

    def test_different_number_of_states_are_not_isomorphic(self):
        m1, _ = build(ALWAYS_COOPERATE)
        m2, _ = build(TIT_FOR_TAT)
        self.assertFalse(m1.is_isomorphic(m2))

    def test_different_outcomes_are_not_isomorphic(self):
        m1, _ = build(ALWAYS_COOPERATE)
        m2, _ = build(ALWAYS_DEFECT)
        self.assertFalse(m1.is_isomorphic(m2))

    def test_different_transition_structure_is_not_isomorphic(self):
        m1, _ = build(TIT_FOR_TAT)
        # Same outcomes per state, but state "1" loops back to itself instead of "0".
        m2, _ = build("0: C, 0, 1\n1: D, 1, 1")
        self.assertFalse(m1.is_isomorphic(m2))


class JsonDataTests(SimpleTestCase):
    def test_same_c_and_d_target_produces_single_cd_edge(self):
        machine, _ = build(ALWAYS_COOPERATE)
        data = machine.json_data()
        self.assertIn("label: \"CD\"", data)
        self.assertNotIn("label: \"C\"", data)

    def test_different_c_and_d_targets_produce_two_edges(self):
        machine, _ = build(TIT_FOR_TAT)
        data = machine.json_data()
        self.assertIn("label: \"C\"", data)
        self.assertIn("label: \"D\"", data)

    def test_initial_state_flagged_true(self):
        machine, _ = build(TIT_FOR_TAT)
        data = machine.json_data()
        self.assertIn('init: "True"', data)
        self.assertIn('init: "False"', data)

    def test_state_first_discovered_through_a_cooperate_transition_is_included(self):
        # State "1" is only ever referenced as a "C" target (never as a "D" target), so this
        # exercises the next_state_coop-not-yet-seen branch specifically.
        machine, _ = build("0: D, 1, 0\n1: C, 1, 0")
        data = machine.json_data()
        # One "name" key per node in the node list: both states should be present.
        self.assertEqual(data.count("name:"), 2)


class StrTests(SimpleTestCase):
    def test_str_includes_initial_state_and_transitions(self):
        machine, _ = build(TIT_FOR_TAT)
        text = str(machine)
        self.assertIn("Init: 0", text)
        self.assertIn("State 0:", text)
        self.assertIn("Out: C", text)
        self.assertIn("State 1:", text)
        self.assertIn("Out: D", text)


class FormatJsonTests(SimpleTestCase):
    def test_integer_valued_float_is_rendered_without_decimals(self):
        self.assertEqual(format_json(3.0), 3)

    def test_non_integer_float_is_rendered_as_is(self):
        self.assertEqual(format_json(3.5), 3.5)

    def test_non_numeric_string_is_quoted(self):
        self.assertEqual(format_json("True"), '"True"')


class FightTests(SimpleTestCase):
    def test_always_cooperate_vs_always_cooperate(self):
        m1, _ = build(ALWAYS_COOPERATE)
        m2, _ = build(ALWAYS_COOPERATE)
        outcomes1, outcomes2 = fight(m1, m2, 3)
        self.assertEqual(outcomes1, ["C", "C", "C"])
        self.assertEqual(outcomes2, ["C", "C", "C"])

    def test_always_defect_vs_always_cooperate(self):
        m1, _ = build(ALWAYS_DEFECT)
        m2, _ = build(ALWAYS_COOPERATE)
        outcomes1, outcomes2 = fight(m1, m2, 3)
        self.assertEqual(outcomes1, ["D", "D", "D"])
        self.assertEqual(outcomes2, ["C", "C", "C"])

    def test_tit_for_tat_vs_always_defect(self):
        m1, _ = build(TIT_FOR_TAT)
        m2, _ = build(ALWAYS_DEFECT)
        outcomes1, outcomes2 = fight(m1, m2, 4)
        # Tit-for-tat cooperates first, then mirrors the opponent's previous defection.
        self.assertEqual(outcomes1, ["C", "D", "D", "D"])
        self.assertEqual(outcomes2, ["D", "D", "D", "D"])

    def test_zero_rounds_produces_empty_outcomes(self):
        m1, _ = build(ALWAYS_COOPERATE)
        m2, _ = build(ALWAYS_COOPERATE)
        outcomes1, outcomes2 = fight(m1, m2, 0)
        self.assertEqual(outcomes1, [])
        self.assertEqual(outcomes2, [])
