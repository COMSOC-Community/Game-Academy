from django import forms

from numbersgame.models import Answer


class SubmitAnswerForm(forms.Form):
    answer = forms.FloatField(min_value=0.0, max_value=100.0, localize=True)
    motivation = forms.CharField(widget=forms.Textarea())

    def __init__(self, *args, **kwargs):
        self.game = kwargs.pop('game', None)
        self.player = kwargs.pop('player', None)
        super(SubmitAnswerForm, self).__init__(*args, **kwargs)

    def clean(self):
        cleaned_data = super(SubmitAnswerForm, self).clean()
        errors = []
        if Answer.objects.filter(player=self.player, game=self.game).exists():
            raise forms.ValidationError("You have already submitted an answer for this game !")
        if 'answer' not in cleaned_data:
            errors.append("The format of your answer is not correct")
        if 0 > cleaned_data['answer'] > 100:
            errors.append("The number should be between 0 and 100")
        return cleaned_data
