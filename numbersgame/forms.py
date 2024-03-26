from django import forms

from numbersgame.models import Answer, Setting


class SettingForm(forms.ModelForm):
    class Meta:
        model = Setting
        exclude = ["game"]

    def num_repetitions(self):
        num_repetitions = self.cleaned_data.get('num_repetitions')
        if ',' in num_repetitions:
            repetitions = [s.strip() for s in num_repetitions.split(",")]
            for r in repetitions:
                try:
                    num_repetitions = float(r)
                except ValueError:
                    raise forms.ValidationError("The number of repetitions needs to be cast as a"
                                                f"float. This failed for value '{r}'.")
            num_repetitions = ",".join(repetitions)
        else:
            num_repetitions = num_repetitions.strip()
            try:
                num_repetitions = float(num_repetitions)
            except ValueError:
                raise forms.ValidationError("The number of repetitions needs to be cast as a"
                                            f"float. This failed for value '{num_repetitions}'.")
        return num_repetitions


class SubmitAnswerForm(forms.Form):
    answer = forms.FloatField(label_suffix="")
    motivation = forms.CharField(label_suffix="", widget=forms.Textarea())

    def __init__(self, *args, **kwargs):
        self.game = kwargs.pop("game", None)
        self.player = kwargs.pop("player", None)
        super(SubmitAnswerForm, self).__init__(*args, **kwargs)

    def clean_answer(self):
        if "answer" not in self.cleaned_data:
            raise forms.ValidationError("The format of your answer is not correct")
        answer = self.cleaned_data["answer"]
        if self.game.numbers_setting.lower_bound > answer or answer > self.game.numbers_setting.upper_bound:
            raise forms.ValidationError(f"The number should be between {self.game.numbers_setting.lower_bound} "
                                        f"and {self.game.numbers_setting.upper_bound}")
        return answer

    def clean(self):
        cleaned_data = super(SubmitAnswerForm, self).clean()
        if Answer.objects.filter(player=self.player, game=self.game).exists():
            raise forms.ValidationError(
                "You have already submitted an answer for this game!"
            )
        return cleaned_data
