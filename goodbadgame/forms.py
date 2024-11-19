from django import forms

from .models import Setting


class SettingForm(forms.ModelForm):
    class Meta:
        model = Setting
        exclude = ["game"]
        widgets = {
            "questions":  forms.widgets.CheckboxSelectMultiple(attrs={'style': 'width: auto;'})
        }
