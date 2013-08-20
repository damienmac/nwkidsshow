from django import forms
from django.forms import ModelForm
from django.forms.widgets import CheckboxSelectMultiple
from django.contrib.auth.models import User
from django.core.exceptions import ObjectDoesNotExist
from django.utils import timezone

from nwkidsshow.models import Show, Exhibitor, Retailer

import datetime
from Pacific_tzinfo import pacific_tzinfo

class ExhibitorRegistrationForm(forms.Form):
    show = forms.ModelChoiceField(queryset=Show.objects.none(), required=True, initial=0, label='Pick a show')
    num_associates = forms.IntegerField(required=True,  min_value=1, max_value=1,  initial=1, label='Exhibitors')
    num_assistants = forms.IntegerField(required=False, min_value=0, max_value=20, initial=0, label='Assistants')
    num_racks      = forms.IntegerField(required=False, min_value=0, max_value=20, initial=0, label='Racks')
    num_tables     = forms.IntegerField(required=False, min_value=0, max_value=20, initial=0, label='Tables')
    
    def __init__(self, request=None, show=None, initial=None):
        if request:
            super(ExhibitorRegistrationForm, self).__init__(request, initial=initial)
        else:
            super(ExhibitorRegistrationForm, self).__init__(initial=initial)
        # self.fields['show'].queryset = Show.objects.filter(closed_date__gte=timezone.localtime(timezone.now(), pacific_tzinfo))
        self.fields['show'].queryset = show


class RetailerRegistrationForm(forms.Form):
    show = forms.ModelChoiceField(queryset=Show.objects.none(), required=True, initial=0, label='Pick a show')
    num_attendees = forms.IntegerField(required=True, min_value=1, max_value=20, initial=1, label='Attendees')
    choices = [(0, 'Day 1'),
               (1, 'Day 2'),
               (2, 'Day 3'),]
    days_attending = forms.MultipleChoiceField(choices=choices,
                                               required=True,
                                               widget=CheckboxSelectMultiple,
                                               initial=choices[0],
                                               label='Choose days')

    def __init__(self, request=None, show=None, initial=None, better_choices=None):
        if request:
            super(RetailerRegistrationForm, self).__init__(request, initial=initial)
        else:
            super(RetailerRegistrationForm, self).__init__(initial=initial)
        # self.fields['show'].queryset = Show.objects.filter(end_date__gte=timezone.localtime(timezone.now(), pacific_tzinfo))
        self.fields['show'].queryset = show
        if better_choices:
            self.choices = better_choices
            self.fields['days_attending'].choices = self.choices

class AddUserForm(forms.Form):
    username      = forms.CharField(max_length=30, label='Login ID')
    password      = forms.CharField(max_length=30, label='Password', initial='password')
    first_name    = forms.CharField(max_length=30, label='First Name')
    last_name     = forms.CharField(max_length=30, label='Last Name')
    email         = forms.EmailField(label='Email', required=False)
    attendee_type = forms.ChoiceField(choices=[('exhibitor','Exhibitor'),
                                               ('retailer','Retailer')],
                                      label='Type',
                                      widget=forms.RadioSelect())

    def clean_username(self):
        username = self.cleaned_data['username']
        try:
            u = User.objects.get(username=username)
        except ObjectDoesNotExist:
            # print "will be creating user: %s" % username
            return username
        msg = 'username "%s" already exists (%s)' % (u.username, u.get_full_name())
        # print msg
        raise forms.ValidationError(msg)


class ExhibitorForm(ModelForm):
    first_name = forms.CharField(max_length=30)
    last_name  = forms.CharField(max_length=30)
    email      = forms.EmailField()
    class Meta:
        model = Exhibitor
        exclude = ('user', 'lines', )


class RetailerForm(ModelForm):
    first_name = forms.CharField(max_length=30)
    last_name  = forms.CharField(max_length=30)
    email      = forms.EmailField()
    class Meta:
        model = Retailer
        exclude = ('user', )


class ExhibitorLinesForm(forms.Form):
    def __init__(self, request=None, num_lines=None, extra_empty=3, *args, **kwargs):
        if request:
            super(ExhibitorLinesForm, self).__init__(request, *args, **kwargs)
        else:
            super(ExhibitorLinesForm, self).__init__(*args, **kwargs)
        for i in xrange(1, num_lines + extra_empty + 1):
            self.fields['line_%i' % i] = forms.CharField(required=False, max_length=100)


class RetailerReportForm(forms.Form):
    show = forms.ModelChoiceField(queryset=Show.objects.none(), required=True, initial=0, label='Pick a show')
    def __init__(self, request=None, shows=None, initial=None, exhibitor=None):
        if request:
            super(RetailerReportForm, self).__init__(request, initial=initial)
        else:
            super(RetailerReportForm, self).__init__(initial=initial)
        # self.fields['show'].queryset = Show.objects.filter(exhibitors=exhibitor)
        self.fields['show'].queryset = shows

class ExhibitorReportForm(forms.Form):
    show = forms.ModelChoiceField(queryset=Show.objects.none(), required=True, initial=0, label='Pick a show')
    def __init__(self, request=None, shows=None, initial=None, retailer=None):
        if request:
            super(ExhibitorReportForm, self).__init__(request, initial=initial)
        else:
            super(ExhibitorReportForm, self).__init__(initial=initial)
        # self.fields['show'].queryset = Show.objects.filter(retailers=retailer)
        self.fields['show'].queryset = shows

