from django import forms
from django.contrib.auth.models import User
from material import Layout, TabularInline, Row
from material.frontend.forms import FormSet
from material.frontend.views import CreateModelView


class EmergencyContractForm(forms.Form):
    name = forms.CharField()
    relationship = forms.ChoiceField(choices=(
        ('SPS', 'Spouse'), ('PRT', 'Partner'),
        ('FRD', 'Friend'), ('CLG', 'Colleague')))
    daytime_phone = forms.CharField()
    evening_phone = forms.CharField(required=False)


class EmergencyContractFormset(FormSet):
    form = EmergencyContractForm
    can_order = False
    can_delete = True
    min_num = 0
    max_num = 1000
    absolute_max = 1000
    validate_min = False
    validate_max = False
    extra = 1


class CreateUserView(CreateModelView):
    model = User
    fields = (
        'username', 'first_name', 'last_name',
        'is_staff', 'is_superuser'
    )
    layout = Layout(
        'username',
        Row('first_name', 'last_name'),
        TabularInline('Emergency Contacts', 'contacts'))
    formsets = {
        'contacts': EmergencyContractFormset
    }
