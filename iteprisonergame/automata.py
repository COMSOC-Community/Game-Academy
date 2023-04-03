class MooreMachine:

    def __init__(self):
        self.current_state = ""
        self.transitions = dict()

    def add_transition(self, state, input_symbol, next_state, output_symbol):
        if state not in self.transitions:
            self.transitions[state] = dict()
        if next_state not in self.transitions:
            self.transitions[next_state] = dict()
        self.transitions[state][input_symbol] = (next_state, output_symbol)

    def test_validity(self, input_alphabet):
        errors = []
        for state in self.transitions:
            for input_symbol in input_alphabet:
                if input_symbol in self.transitions[state]:
                    next_state = self.transitions[state][input_symbol][0]
                    if next_state not in self.transitions:
                        errors.append("The state {} reached from ({}, {}) is not a known state.".format(next_state,
                                                                                                        state,
                                                                                                        input_symbol))
                else:
                    errors.append("No transition is specified for state {} and symbol {}.".format(state,
                                                                                                  input_symbol))
        return errors

    def transition(self, input_symbol):
        (next_state, output) = self.transitions[self.current_state][input_symbol]
        self.current_state = next_state
        return output
