import re

from django import forms

from iteprisonergame.models import Answer


class SubmitAnswerForm(forms.Form):
    name = forms.CharField(label="Name of the strategy")
    number_states = forms.IntegerField(min_value=1, label='Number of states')
    automata = forms.CharField(widget=forms.Textarea())
    motivation = forms.CharField(widget=forms.Textarea(), required=False)

    def __init__(self, *args, **kwargs):
        self.game = kwargs.pop('game', None)
        self.team = kwargs.pop('team', None)
        super(SubmitAnswerForm, self).__init__(*args, **kwargs)

    def clean(self):
        cleaned_data = super(SubmitAnswerForm, self).clean()
        print(self.team)
        print(self.game)
        print(Answer.objects.filter(team=self.team, game=self.game))
        if Answer.objects.filter(team=self.team, game=self.game).exists():
            raise forms.ValidationError("This team already submitted an answer for this game !")
        pattern = re.compile("^ *[CD], *([0-9]+), *([0-9]+)$")
        lines = cleaned_data['answer'].strip().split('\n')
        if len(lines) != cleaned_data["number_states"]:
            raise forms.ValidationError("The number of lines in the answer " +
                                        "does not match the number of states given above.")
        for i in range(len(lines)):
            m = pattern.search(lines[i].strip())
            if m:
                for g in m.groups():
                    if int(g) >= cleaned_data['number_states']:
                        raise forms.ValidationError("The state name on line " + str(i + 1) +
                                                    " exceed the number of states (" + str(
                            cleaned_data["number_states"]) +
                                                    ") given above, the state name should be between 0 and " +
                                                    str(cleaned_data["numberStates"] - 1) + ".")
            else:
                raise forms.ValidationError("The line number " + str(i + 1) +
                                            " seems not to follow the correct syntax, check it carefully. " +
                                            "Remember that it should follow the regular expression " +
                                            "^ *[CD], *([0-9]+), *([0-9]+)$.")
        return cleaned_data
