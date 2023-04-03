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

    def test_validity(self, input_alphabet):
        errors = []
        for state in self.transitions:
            for input_symbol in input_alphabet:
                if input_symbol in self.transitions[state]:
                    next_state = self.transitions[state][input_symbol]
                    if next_state not in self.transitions:
                        errors.append("The state {} reached from ({}, {}) is not a known state.".format(next_state,
                                                                                                        state,
                                                                                                        input_symbol))
                else:
                    errors.append("No transition is specified for state {} and symbol {}.".format(state,
                                                                                                  input_symbol))
        return errors

    def transition(self, input_symbol):
        self.current_state = self.transitions[self.current_state][input_symbol]

    def __str__(self):
        res = "Init: {}\n".format(self.initial_state)
        for state in self.transitions:
            res += "State {}:\n\tOut: {}\n".format(state, self.outcome[state])
            for symbol in self.transitions[state]:
                res += "\t{} -> {}\n".format(symbol, self.transitions[state][symbol])
        return res


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
