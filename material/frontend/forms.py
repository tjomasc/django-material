from django import forms
from django.forms import BaseFormSet


class DatatableRequestForm(forms.Form):
    draw = forms.IntegerField()
    start = forms.IntegerField()
    length = forms.IntegerField()


class FormSet(BaseFormSet):
    can_order = False
    can_delete = True
    min_num = 0
    max_num = 1000
    absolute_max = 1000
    validate_min = False
    validate_max = False
    extra = 1
