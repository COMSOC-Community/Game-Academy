from django import forms

from simp_poker.models import Answer, Setting


# class SettingForm(forms.ModelForm):
#     class Meta:
#         model = Setting
#         exclude = ["game"]


class SubmitAnswerForm(forms.Form):
    prob_p1_king = forms.FloatField(
        label_suffix="",
        label="Probability of betting when king",
        help_text="The probability of betting when, as player 1, you are holding a king.",
        min_value=0,
        max_value=1,
    )
    prob_p1_queen = forms.FloatField(
        label_suffix="",
        label="Probability of betting when queen",
        help_text="The probability of betting when, as player 1, you are holding a queen.",
        min_value=0,
        max_value=1,
    )
    prob_p1_jack = forms.FloatField(
        label_suffix="",
        label="Probability of betting when jack",
        help_text="The probability of betting when, as player 1, you are holding a jack.",
        min_value=0,
        max_value=1,
    )
    prob_p2_king = forms.FloatField(
        label_suffix="",
        label="Probability of calling when king",
        help_text="The probability of calling when, as player 2, you are holding a king.",
        min_value=0,
        max_value=1,
    )
    prob_p2_queen = forms.FloatField(
        label_suffix="",
        label="Probability of calling when queen",
        help_text="The probability of calling when, as player 2, you are holding a queen.",
        min_value=0,
        max_value=1,
    )
    prob_p2_jack = forms.FloatField(
        label_suffix="",
        label="Probability of calling when jack",
        help_text="The probability of calling when, as player 2, you are holding a jack.",
        min_value=0,
        max_value=1,
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
