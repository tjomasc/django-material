from django import forms


class DatatableRequestForm(forms.Form):
    draw = forms.IntegerField()
    start = forms.IntegerField()
    length = forms.IntegerField()
