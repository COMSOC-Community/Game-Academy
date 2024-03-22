import re

from django import forms

from iteprisonergame.automata import MooreMachine
from iteprisonergame.models import Answer, Setting


class SettingForm(forms.ModelForm):
    class Meta:
        model = Setting
        exclude = ["game"]

    def clean_histogram_bin_size(self):
        bin_size = self.cleaned_data.get('histogram_bin_size')
        if bin_size <= 0:
            raise forms.ValidationError("The histogram bin size cannot be 0 or less.")
        if bin_size > 100:
            raise forms.ValidationError("The histogram bin size cannot be more than 100.")
        return bin_size


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
        self.player = kwargs.pop("player", None)
        self.moore_machine = None
        super(SubmitAnswerForm, self).__init__(*args, **kwargs)

    def clean_automata(self):
        automata = MooreMachine()
        lines = self.cleaned_data["automata"].strip().split("\n")
        errors = automata.parse(lines)
        if errors:
            raise forms.ValidationError(errors)
        else:
            validity_errors = automata.test_validity(["C", "D"])
            if validity_errors:
                raise forms.ValidationError(validity_errors)
            self.moore_machine = automata
            return self.cleaned_data["automata"]

    def clean(self):
        cleaned_data = super(SubmitAnswerForm, self).clean()
        if self.moore_machine and "initial_state" in cleaned_data:
            connectivity_error = self.moore_machine.test_connectivity(cleaned_data["initial_state"])
            if connectivity_error:
                raise forms.ValidationError(connectivity_error)
        if Answer.objects.filter(player=self.player, game=self.game).exists():
            raise forms.ValidationError(
                "This player already submitted an answer for this game!"
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
