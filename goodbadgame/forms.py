from django import forms
from django.core.exceptions import ValidationError

from .models import *


class PlayerForm(forms.Form):
    name = forms.CharField()

    def __init__(self, *args, **kwargs):
        self.session = kwargs.pop('session', None)
        super(PlayerForm, self).__init__(*args, **kwargs)

    def clean_name(self):
        name = self.cleaned_data['name'].strip()
        if Player.objects.filter(name=name, session=self.session).exists():
            raise ValidationError("A player with this name already exists")
        return name
