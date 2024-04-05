from django import forms

from auctiongame.models import Answer


class SubmitAnswerForm(forms.Form):
    bid = forms.FloatField(
        min_value=0.0,
        label_suffix="",
    )
    motivation = forms.CharField(label_suffix="", widget=forms.Textarea())

    def __init__(self, *args, **kwargs):
        self.game = kwargs.pop("game", None)
        self.player = kwargs.pop("player", None)
        super(SubmitAnswerForm, self).__init__(*args, **kwargs)

    def clean(self):
        cleaned_data = super(SubmitAnswerForm, self).clean()
        answer = Answer.objects.filter(player=self.player, game=self.game)
        if answer.exists():
            answer = answer.first()
            if answer.bid is not None:
                raise forms.ValidationError(
                    "You have already submitted an answer for this game!"
                )
        else:
            raise forms.ValidationError(
                "Your answer object is not initialised, that is weird..."
            )
        return cleaned_data
