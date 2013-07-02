from django import forms

class OrgForm(forms.Form):
    organization = forms.CharField(max_length=100, initial='MadeInHaus')
    days = forms.IntegerField(initial=14)
    