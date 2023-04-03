import re

from django import forms

from iteprisonergame.automata import MooreMachine
from iteprisonergame.models import Answer


class SubmitAnswerForm(forms.Form):
    name = forms.CharField(label="Name of the strategy",
                           label_suffix="")
    automata = forms.CharField(label="Strategy",
                               label_suffix="",
                               widget=forms.Textarea())
    motivation = forms.CharField(label="Motivation",
                                 label_suffix="",
                                 widget=forms.Textarea(), required=False)

    def __init__(self, *args, **kwargs):
        self.game = kwargs.pop('game', None)
        self.team = kwargs.pop('team', None)
        super(SubmitAnswerForm, self).__init__(*args, **kwargs)

    def clean_automata(self):
        automata = MooreMachine()
        pattern = re.compile("^ *([0-9]+), *([CD]), *([0-9]+)$")
        errors = []
        lines = self.cleaned_data['automata'].strip().split('\n')
        for line_index in range(len(lines)):
            match = pattern.search(lines[line_index].strip())
            if match:
                state = match.group(1)
                symbol = match.group(2)
                next_state = match.group(3)
                if state in automata.transitions and symbol in automata.transitions[state]:
                    errors.append("Line {} redefines a transition for state {} and symbol {}.".format(line_index + 1,
                                                                                                      state,
                                                                                                      symbol))
                automata.add_transition(state, symbol, next_state, 0)
            else:
                errors.append("Line {} is not formatted correctly".format(line_index + 1))
        if errors:
            raise forms.ValidationError(errors)
        else:
            validity_errors = automata.test_validity(["C", "D"])
            if validity_errors:
                raise forms.ValidationError(validity_errors)
            return self.cleaned_data['automata']

    def clean(self):
        cleaned_data = super(SubmitAnswerForm, self).clean()
        if Answer.objects.filter(team=self.team, game=self.game).exists():
            raise forms.ValidationError("This team already submitted an answer for this game!")
        return cleaned_data
