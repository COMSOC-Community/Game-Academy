import re

from django import forms

from iteprisonergame.automata import MooreMachine
from iteprisonergame.models import Answer


class SubmitAnswerForm(forms.Form):
    name = forms.CharField(label="Name of the Strategy", label_suffix="")
    initial_state = forms.CharField(
        label="Initial State",
        label_suffix="",
        max_length=Answer._meta.get_field("initial_state").max_length,
    )
    automata = forms.CharField(
        label="Strategy", label_suffix="", widget=forms.Textarea()
    )
    motivation = forms.CharField(
        label="Motivation", label_suffix="", widget=forms.Textarea(), required=False
    )

    def __init__(self, *args, **kwargs):
        self.game = kwargs.pop("game", None)
        self.team = kwargs.pop("team", None)
        super(SubmitAnswerForm, self).__init__(*args, **kwargs)

    def clean_automata(self):
        automata = MooreMachine()
        pattern = re.compile(
            "^[^\S\n]*([0-9]+):[^\S\n\t]*([CD]),[^\S\n\t]*([0-9]+),[^\S\n\t]*([0-9]+)$"
        )
        errors = []
        lines = self.cleaned_data["automata"].strip().split("\n")
        for line_index in range(len(lines)):
            match = pattern.search(lines[line_index].strip())
            if match:
                state = match.group(1)
                action = match.group(2)
                next_state_coop = match.group(3)
                next_state_def = match.group(3)
                if (
                    state in automata.transitions
                    and "C" in automata.transitions[state]
                    and "D" in automata.transitions[state]
                ):
                    errors.append(
                        "Line {} redefines state {}.".format(line_index + 1, state)
                    )
                automata.add_transition(state, "C", next_state_coop)
                automata.add_transition(state, "D", next_state_def)
                automata.add_outcome(state, action)
            else:
                errors.append(
                    "Line {} is not formatted correctly".format(line_index + 1)
                )
        if errors:
            raise forms.ValidationError(errors)
        else:
            validity_errors = automata.test_validity(["C", "D"])
            if validity_errors:
                raise forms.ValidationError(validity_errors)
            return self.cleaned_data["automata"]

    def clean(self):
        cleaned_data = super(SubmitAnswerForm, self).clean()
        if Answer.objects.filter(team=self.team, game=self.game).exists():
            raise forms.ValidationError(
                "This team already submitted an answer for this game!"
            )
        if "automata" in cleaned_data:
            found_initial_state = False
            for line in cleaned_data["automata"].strip().split("\n"):
                if line.split(":")[0].strip() == cleaned_data["initial_state"].strip():
                    found_initial_state = True
            if not found_initial_state:
                raise forms.ValidationError(
                    "The initial state is not part of the states described in the strategy."
                )
        return cleaned_data
