from django.db import models
from django.contrib.auth.models import User


class Attendee(models.Model):
    # Trying to keep this simple - does this work okay?
    # They edit their profile on a PAGE and not in django admin?
    # first_name, last_name, email are in here already
    user = models.OneToOneField(User)
    
    company   = models.CharField(max_length=50)
    website   = models.URLField() # default length is 200
    address   = models.CharField(max_length=50)
    address2  = models.CharField(max_length=50)
    city      = models.CharField(max_length=60)
    state     = models.CharField(max_length=30)
    zip       = models.CharField(max_length=5)
    phone     = models.CharField(max_length=12)
    fax       = models.CharField(max_length=12)

    class Meta:
        # make this an abstract base class which Exhibitor and Retailer can use
        # there will be no Attendee table, just Exhibitor and Retailer tables.
        abstract = True
        ordering = ['user']

    def __unicode__(self):
        return u'%s (%s)' % (self.user.username, self.user.get_full_name())
    
    def first_name_display(self):
        return self.user.first_name
    first_name_display.short_description = 'First Name'

    def last_name_display(self):
        return self.user.last_name
    last_name_display.short_description = 'Last Name'
    
    def email_display(self):
        return self.user.email
    email_display.short_description = 'Email'
    
    def username_display(self):
        return self.user.username
    username_display.short_description = 'Username'


class Exhibitor(Attendee):
    lines = models.TextField() # TODO: find a better model for this, on a per-exhibitor basis.


class Retailer(Attendee):
    # nothing more to add on top of the abstract base class... yet!
    pass


class Show(models.Model):

    name = models.CharField(max_length=50)

    late_date   = models.DateField()  # last day to register without a late fee
    closed_date = models.DateField()  # last day to register
    start_date  = models.DateField()  # start date of the actual show
    end_date    = models.DateField()  # last day of the actual show

    registration_fee = models.FloatField()
    assistant_fee    = models.FloatField() # each assistant
    late_fee         = models.FloatField()
    rack_fee         = models.FloatField() # each rack

    exhibitors = models.ManyToManyField(Exhibitor, blank=True, null=True)
    retailers  = models.ManyToManyField(Retailer, blank=True, null=True)

    def __unicode__(self):
        return u'%s' % self.name

    class Meta:
        ordering = ['closed_date']


class Registration(models.Model):
    show      = models.OneToOneField(Show)
    exhibitor = models.OneToOneField(Exhibitor)

    num_exhibitors  = models.SmallIntegerField()
    num_assistants  = models.SmallIntegerField()
    num_racks       = models.SmallIntegerField()
    num_tables      = models.SmallIntegerField()
    is_late         = models.BooleanField()
    date_registered = models.DateField()

    registration_total = models.FloatField()
    assistant_total    = models.FloatField()
    rack_total         = models.FloatField()
    late_total         = models.FloatField()
    total              = models.FloatField()

    has_paid = models.BooleanField()
