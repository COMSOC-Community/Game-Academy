from django import forms

from numbersgame.models import Answer, Setting


class SettingForm(forms.ModelForm):
    class Meta:
        model = Setting
        exclude = ["game"]

    def clean_histogram_bin_size(self):
        bin_size = self.cleaned_data.get("histogram_bin_size")
        if bin_size <= 0:
            raise forms.ValidationError("The histogram bin size cannot be 0 or less.")
        if bin_size > 100:
            raise forms.ValidationError(
                "The histogram bin size cannot be more than 100."
            )
        return bin_size

    def clean(self):
        cleaned_data = super().clean()
        lower_bound = cleaned_data.get("lower_bound")
        upper_bound = cleaned_data.get("upper_bound")

        if lower_bound is not None and upper_bound is not None:
            if lower_bound > upper_bound:
                raise forms.ValidationError(
                    {"lower_bound": "The lower bound cannot be greater than the upper bound."}
                )

        return cleaned_data


class SubmitAnswerForm(forms.Form):
    answer = forms.FloatField(
        label_suffix="",
    )
    motivation = forms.CharField(label_suffix="", widget=forms.Textarea())

    def __init__(self, *args, **kwargs):
        self.game = kwargs.pop("game", None)
        self.player = kwargs.pop("player", None)
        super(SubmitAnswerForm, self).__init__(*args, **kwargs)

    def clean_answer(self):
        if "answer" not in self.cleaned_data:
            raise forms.ValidationError("The format of your answer is not correct")
        answer = self.cleaned_data["answer"]
        if (
            self.game.numbers_setting.lower_bound > answer
            or answer > self.game.numbers_setting.upper_bound
        ):
            raise forms.ValidationError(
                f"The number should be between {self.game.numbers_setting.lower_bound} "
                f"and {self.game.numbers_setting.upper_bound}"
            )
        return answer

    def clean(self):
        cleaned_data = super(SubmitAnswerForm, self).clean()
        if Answer.objects.filter(player=self.player, game=self.game).exists():
            raise forms.ValidationError(
                "You have already submitted an answer for this game!"
            )
        return cleaned_data
