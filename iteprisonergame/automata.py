import re


class AutomataNotIsomorphicError(ValueError):
    pass


class MooreMachine:
    def __init__(self):
        self.current_state = ""
        self.initial_state = ""
        self.outcome = dict()
        self.transitions = dict()

    def add_transition(self, state, input_symbol, next_state):
        if state not in self.transitions:
            self.transitions[state] = dict()
        if next_state not in self.transitions:
            self.transitions[next_state] = dict()
        self.transitions[state][input_symbol] = next_state

    def add_outcome(self, state, symbol):
        self.outcome[state] = symbol

    def parse_from_answer(self, answer):
        self.initial_state = answer.initial_state.strip()
        return self.parse(answer.automata.strip().split("\n"))

    def parse(self, lines):
        pattern = re.compile(
            "^[^\S\n]*([A-Za-z0-9]+):[^\S\n\t]*([CD]),[^\S\n\t]*([A-Za-z0-9]+),[^\S\n\t]*([A-Za-z0-9]+)$"
        )
        errors = []
        for line_index in range(len(lines)):
            match = pattern.search(lines[line_index].strip())
            if match:
                state = match.group(1)
                action = match.group(2)
                next_state_coop = match.group(3)
                next_state_def = match.group(4)
                if (
                    state in self.transitions
                    and "C" in self.transitions[state]
                    and "D" in self.transitions[state]
                ):
                    errors.append(
                        "Line {} redefines state {}.".format(line_index + 1, state)
                    )
                self.add_transition(state, "C", next_state_coop)
                self.add_transition(state, "D", next_state_def)
                self.add_outcome(state, action)
            else:
                errors.append(
                    "Line {} is not formatted correctly".format(line_index + 1)
                )
        return errors

    def test_validity(self, input_alphabet):
        errors = []
        for state in self.transitions:
            for input_symbol in input_alphabet:
                if input_symbol in self.transitions[state]:
                    next_state = self.transitions[state][input_symbol]
                    if next_state not in self.transitions:
                        errors.append(
                            "The state {} reached from ({}, {}) is not a known state.".format(
                                next_state, state, input_symbol
                            )
                        )
                else:
                    errors.append(
                        "No transition is specified for state {} and symbol {}.".format(
                            state, input_symbol
                        )
                    )
        return errors

    def test_connectivity(self):
        def aux(state):
            if state not in visited_states:
                visited_states.add(state)
                for input_symbol, next_state in self.transitions[state].items():
                    aux(next_state)

        visited_states = set()
        aux(self.initial_state)

        if len(visited_states) != len(self.transitions):
            unconnected_states = sorted(
                s for s in self.transitions if s not in visited_states
            )
            if unconnected_states:
                return (
                    f"The automata is composed of more than one connected components. From "
                    f"the initial state '{self.initial_state} ' the following states could "
                    f"not be reached: {' '.join(unconnected_states)}"
                )

    def transition(self, input_symbol):
        self.current_state = self.transitions[self.current_state][input_symbol]

    def is_isomorphic(self, other_automata):
        def aux(self_state, other_state):
            if self.outcome[self_state] != other_automata.outcome[other_state]:
                raise AutomataNotIsomorphicError("The automatas are not isomorphic")
            state_renaming[self_state] = other_state
            for input_symbol in ("C", "D"):
                self_next_state = self.transitions[self_state][input_symbol]
                other_next_state = other_automata.transitions[other_state][input_symbol]
                # print(self_state, other_state, input_symbol, self_next_state, other_next_state)
                if self_next_state in state_renaming:
                    if state_renaming[self_next_state] != other_next_state:
                        raise AutomataNotIsomorphicError(
                            "The automatas are not isomorphic"
                        )
                else:
                    state_renaming[self_next_state] = other_next_state
                    aux(self_next_state, other_next_state)

        if len(self.transitions) != len(other_automata.transitions):
            return False

        state_renaming = {self.initial_state: other_automata.initial_state}
        try:
            aux(self.initial_state, other_automata.initial_state)
        except AutomataNotIsomorphicError:
            return False
        return True

    def json_data(self):
        seen_states = set()
        state_list = []
        nodes = []
        links = []
        for state, transition in self.transitions.items():
            if state not in seen_states:
                state_list.append(state)
                seen_states.add(state)
            next_state_coop = transition["C"]
            if next_state_coop not in seen_states:
                state_list.append(next_state_coop)
                seen_states.add(next_state_coop)
            next_state_def = transition["D"]
            if next_state_def not in seen_states:
                state_list.append(next_state_def)
                seen_states.add(next_state_def)
            nodes.append(
                {
                    "id": state_list.index(state),
                    "name": self.outcome[state],
                    "init": str(state == self.initial_state),
                }
            )
            if next_state_coop == next_state_def:
                links.append(
                    {
                        "id": len(links),
                        "source": state_list.index(state),
                        "target": state_list.index(next_state_coop),
                        "label": "CD",
                    }
                )
            else:
                links.append(
                    {
                        "id": len(links),
                        "source": state_list.index(state),
                        "target": state_list.index(next_state_coop),
                        "label": "C",
                    }
                )
                links.append(
                    {
                        "id": len(links),
                        "source": state_list.index(state),
                        "target": state_list.index(next_state_def),
                        "label": "D",
                    }
                )
        json_data = "{nodes: ["
        for node in nodes:
            json_data += "{"
            for key in node:
                json_data += "{}: {}, ".format(key, format_json(node[key]))
            json_data = json_data[:-2] + "}, "
        json_data = json_data[:-2] + "], edges: ["
        for link in links:
            json_data += "{"
            for key in link:
                json_data += "{}: {}, ".format(key, format_json(link[key]))
            json_data = json_data[:-2] + "}, "
        json_data = json_data[:-2] + "]}"
        return json_data

    def __str__(self):
        res = "Init: {}\n".format(self.initial_state)
        for state in self.transitions:
            res += "State {}:\n\tOut: {}\n".format(state, self.outcome[state])
            for symbol in self.transitions[state]:
                res += "\t{} -> {}\n".format(symbol, self.transitions[state][symbol])
        return res


def format_json(x):
    try:
        y = int(x)
        if y == x:
            return int(x)
        return x
    except ValueError:
        return '"' + str(x).strip() + '"'


def fight(automata1, automata2, number_rounds):
    automata1.current_state = automata1.initial_state
    automata2.current_state = automata2.initial_state

    outcomes1 = []
    outcomes2 = []

    for round_index in range(number_rounds):
        outcome1 = automata1.outcome[automata1.current_state]
        outcome2 = automata2.outcome[automata2.current_state]
        outcomes1.append(outcome1)
        outcomes2.append(outcome2)

        automata1.transition(outcome2)
        automata2.transition(outcome1)
    return outcomes1, outcomes2
