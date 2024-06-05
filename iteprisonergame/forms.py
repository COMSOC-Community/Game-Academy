from django import forms

from iteprisonergame.automata import MooreMachine
from iteprisonergame.models import Answer, Setting


class SettingForm(forms.ModelForm):
    class Meta:
        model = Setting
        exclude = ["game"]

    def clean_num_repetitions(self):
        num_repetitions = self.cleaned_data.get("num_repetitions")
        if "," in num_repetitions:
            repetitions = [s.strip() for s in num_repetitions.split(",")]
            for r in repetitions:
                try:
                    float(r)
                except ValueError:
                    raise forms.ValidationError(
                        "The numbers of repetitions need to be cast as a "
                        f"float. This failed for value '{r}'."
                    )
            num_repetitions = ",".join(repetitions)
        else:
            num_repetitions = num_repetitions.strip()
            try:
                num_repetitions = float(num_repetitions)
            except ValueError:
                raise forms.ValidationError(
                    "The number of repetitions needs to be cast as a "
                    f"float. This failed for value '{num_repetitions}'."
                )
        return num_repetitions


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
        self.game = kwargs.pop("game")
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
            if self.moore_machine:
                self.moore_machine.initial_state = cleaned_data["initial_state"]
                connectivity_error = self.moore_machine.test_connectivity()
                if connectivity_error:
                    raise forms.ValidationError(connectivity_error)
            if self.game.itepris_setting.forbidden_strategies:
                forbidden_strategies = []
                current_strategy = []
                for line in self.game.itepris_setting.forbidden_strategies.split("\n"):
                    line = line.strip()
                    if len(line) > 0:
                        if line.startswith("---"):
                            forbidden_strategies.append(current_strategy)
                            current_strategy = []
                        else:
                            current_strategy.append(line)
                if current_strategy:
                    forbidden_strategies.append(current_strategy)
                for s in forbidden_strategies:
                    m = MooreMachine()
                    m.parse(s)
                    m.initial_state = s[0].split(':')[0].strip()
                    if m.is_isomorphic(self.moore_machine):
                        raise forms.ValidationError("The admin of this session has forbidden this "
                                                    "strategy, please submit another one.")

        return cleaned_data
