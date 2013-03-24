from django import forms
from django.forms.widgets import CheckboxSelectMultiple
from nwkidsshow.models import Show
import datetime

class ExhibitorRegistrationForm(forms.Form):
    show = forms.ModelChoiceField(queryset=Show.objects.none(), required=True, initial=0, label='Pick a show')
    num_associates = forms.IntegerField(required=False, min_value=1, max_value=20, initial=1, label='Exhibitors')
    num_assistants = forms.IntegerField(required=False, min_value=0, max_value=20, initial=0, label='Assistants')
    num_racks      = forms.IntegerField(required=False, min_value=0, max_value=20, initial=0, label='Racks')
    num_tables     = forms.IntegerField(required=False, min_value=0, max_value=20, initial=0, label='Tables')
    
    def __init__(self, request=None):
        if request:
            super(ExhibitorRegistrationForm, self).__init__(request)
        else:
            super(ExhibitorRegistrationForm, self).__init__()
        self.fields['show'].queryset = Show.objects.filter(closed_date__gt=datetime.date.today())

class RetailerRegistrationForm(forms.Form):
    show = forms.ModelChoiceField(queryset=Show.objects.none(), required=True, initial=0, label='Pick a show')
    num_attendees = forms.IntegerField(required=False, min_value=1, max_value=20, initial=1, label='Attendees')
    choices = [(1, 'Day 1'),
               (2, 'Day 2'),
               (3, 'Day 3'),]
    days_attending = forms.MultipleChoiceField(choices=choices,
                                               required=True,
                                               widget=CheckboxSelectMultiple,
                                               initial=choices[0],
                                               label='Choose days')

    def __init__(self, request=None, better_choices=None):
        if request:
            super(RetailerRegistrationForm, self).__init__(request)
        else:
            super(RetailerRegistrationForm, self).__init__()
        self.fields['show'].queryset = Show.objects.filter(closed_date__gt=datetime.date.today())
        if better_choices:
            self.choices = better_choices
            self.fields['days_attending'].choices = self.choices
