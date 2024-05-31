from django import forms
from django.core.exceptions import ValidationError

from .models import Setting


class SettingForm(forms.ModelForm):
    class Meta:
        model = Setting
        exclude = ["game"]
