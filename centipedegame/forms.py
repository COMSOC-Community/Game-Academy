from django import forms

from centipedegame.constants import CENTIPEDE_STRATEGIES
from centipedegame.models import Answer, Setting


class SettingForm(forms.ModelForm):
    class Meta:
        model = Setting
        exclude = ["game"]


class SubmitAnswerForm(forms.Form):
    strategy_as_p1 = forms.ChoiceField(
        choices=[("", "----")] + list(zip(CENTIPEDE_STRATEGIES, CENTIPEDE_STRATEGIES)),
        label="Strategy as Player 1",
        label_suffix="",
        required=True,
    )
    strategy_as_p2 = forms.ChoiceField(
        choices=[("", "----")] + list(zip(CENTIPEDE_STRATEGIES, CENTIPEDE_STRATEGIES)),
        label="Strategy as Player 2",
        label_suffix="",
    )
    motivation = forms.CharField(label_suffix="", widget=forms.Textarea())

    def __init__(self, *args, **kwargs):
        self.game = kwargs.pop("game", None)
        self.player = kwargs.pop("player", None)
        super(SubmitAnswerForm, self).__init__(*args, **kwargs)

    def clean(self):
        cleaned_data = super(SubmitAnswerForm, self).clean()
        if Answer.objects.filter(player=self.player, game=self.game).exists():
            raise forms.ValidationError(
                "You have already submitted an answer for this game!"
            )
        return cleaned_data
