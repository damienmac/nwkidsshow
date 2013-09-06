
# django request/response stuff
from django.forms.models import model_to_dict
from django.http import HttpResponse
from django.http import HttpResponseRedirect
from django.shortcuts import render_to_response, redirect
from django.template import RequestContext
from django.utils import timezone

# django exceptions
from django.core.exceptions import ObjectDoesNotExist

# django authentication
from django.contrib.auth.models import User, Group
from django.contrib.auth.decorators import login_required, user_passes_test
from django.contrib.auth.views import password_change
from django.contrib.admin.views.decorators import staff_member_required

# my models
from nwkidsshow.models import Exhibitor
from nwkidsshow.models import Retailer
from nwkidsshow.models import Show
from nwkidsshow.models import Registration
from nwkidsshow.models import RetailerRegistration

# my forms
from nwkidsshow.forms import ExhibitorRegistrationForm, RetailerRegistrationForm
from nwkidsshow.forms import ExhibitorForm, RetailerForm
from nwkidsshow.forms import ExhibitorLinesForm
from nwkidsshow.forms import RetailerReportForm
from nwkidsshow.forms import ExhibitorReportForm
from nwkidsshow.forms import AddUserForm
from nwkidsshow.forms import CheckoutForm

# django query stuff
from django.db.models import Q

# my excel exporting methods
from nwkidsshow.excel import exhibitor_xls, exhibitor_lines_xls, retailer_xls

# info from settings.py I might need here...
from settings import running_in_prod

# credit card processing stuff
import braintree

# python stuff
import logging
logger = logging.getLogger(__name__)
import datetime
from Pacific_tzinfo import pacific_tzinfo
from pprint import pprint

### notes ###
#TODO: I need test accounts that are not real users: "testex" and "testret". Need to hide them from reports, but otherwise work like a real user.
#TODO: why is it looking for this on retailer login? "GET /retailer/home/css/messages.css HTTP/1.1" 404 2991
#TODO: why is it looking for this on exhibitor login?  "GET /exhibitor/home/css/messages.css HTTP/1.1" 404 2994
#TODO: no-cache on our pages? how? Laurie was seeing cached pages on FF.

### helpers ###

def user_is_exhibitor(user):
    if user:
        return user.groups.filter(name='exhibitor_group').exists()
    return False

def user_is_retailer(user):
    if user:
        return user.groups.filter(name='retailer_group').exists()
    return False

def user_is_exhibitor_or_retailer(user):
    if user:
        return user.groups.filter(Q(name='exhibitor_group') | Q(name='retailer_group')).exists()
    return False

def get_user(request):
    try:
        user = Retailer.objects.get(user=request.user)
    except ObjectDoesNotExist:
        user = None
    if not user:
        try:
            user = Exhibitor.objects.get(user=request.user)
        except ObjectDoesNotExist:
            user = None
    return user

DEFAULT_VENUE = 'nw'

venue_map = {
    'localhost:8080'        : 'nwkidsshow',
    'localhost:8181'        : 'cakidsshow',

    'nwkidsshow'            : 'nwkidsshow',
    'nwkidsshow.com'        : 'nwkidsshow',
    'nwkidsshow:80'         : 'nwkidsshow',
    'nwkidsshow.com:80'     : 'nwkidsshow',
    'www.nwkidsshow'        : 'nwkidsshow',
    'www.nwkidsshow.com'    : 'nwkidsshow',
    'www.nwkidsshow:80'     : 'nwkidsshow',
    'www.nwkidsshow.com:80' : 'nwkidsshow',

    'cakidsshow'            : 'cakidsshow',
    'cakidsshow.com'        : 'cakidsshow',
    'cakidsshow:80'         : 'cakidsshow',
    'cakidsshow.com:80'     : 'cakidsshow',
    'www.cakidsshow'        : 'cakidsshow',
    'www.cakidsshow.com'    : 'cakidsshow',
    'www.cakidsshow:80'     : 'cakidsshow',
    'www.cakidsshow.com:80' : 'cakidsshow',
}

def _get_venue(request):
    host = request.META['HTTP_HOST'] or ''
    # return venue_map.get(host, DEFAULT_VENUE)
    try:
        return venue_map[host]
    except KeyError:
        logger.error('Could not find a venue mapping for domain "%s"' % host)
    return DEFAULT_VENUE

def venue_context(request):
    return {'venue': _get_venue(request), }

CKS_DEFAULT_BANNER  = ('cks-banner-left.png', 'cks-banner-hooper-01.png',)
NWKS_DEFAULT_BANNER = ('cks-banner-left.png', 'cks-banner-hooper-01.png',)

banner_map = {
    'nwkidsshow': {
        '/':                 ('nwks-banner-left.png', 'cks-banner-hooper-01.png',),

        '/contact/':         ('nwks-banner-left.png', 'cks-banner-polkadot-01.png',),

        '/about/':           ('nwks-banner-left.png', 'cks-banner-snowangel-01.png',),
        '/privacy-policy/':  ('nwks-banner-left.png', 'cks-banner-snowangel-01.png',),

        '/accounts/':        ('nwks-banner-left.png', 'cks-banner-dad-01.png',),

        '/advising/':        ('nwks-banner-left.png', 'cks-banner-paint-01.png',),

        '/exhibitor/home/':  ('nwks-banner-left.png', 'cks-banner-dancers-01.png',),
        '/retailer/home/':   ('nwks-banner-left.png', 'cks-banner-dancers-01.png',),

        '/register/':        ('nwks-banner-left.png', 'cks-banner-handstand-01.png',),
        '/checkout/':        ('nwks-banner-left.png', 'cks-banner-handstand-01.png',),
        '/registered/':      ('nwks-banner-left.png', 'cks-banner-handstand-01.png',),

        '/invoices/':        ('nwks-banner-left.png', 'cks-banner-poodle-01.png',),
        '/invoice/':         ('nwks-banner-left.png', 'cks-banner-poodle-01.png',),
        '/registrations/':   ('nwks-banner-left.png', 'cks-banner-poodle-01.png',),

        '/lines/':           ('nwks-banner-left.png', 'cks-banner-yellow-01.png',),

        '/edit/':            ('nwks-banner-left.png', 'cks-banner-dino1-01.png',),

        '/report/':          ('nwks-banner-left.png', 'cks-banner-camera-01.png',),

        '/exhibitors/':      ('nwks-banner-left.png', 'cks-banner-snowhat-01.png',),
    },
    'cakidsshow': {
        '/':                 ('cks-banner-left.png', 'cks-banner-hooper-01.png',),

        '/contact/':         ('cks-banner-left.png', 'cks-banner-polkadot-01.png',),

        '/about/':           ('cks-banner-left.png', 'cks-banner-snowangel-01.png',),
        '/privacy-policy/':  ('cks-banner-left.png', 'cks-banner-snowangel-01.png',),

        '/accounts/':        ('cks-banner-left.png', 'cks-banner-dad-01.png',),

        '/advising/':        ('cks-banner-left.png', 'cks-banner-paint-01.png',),

        '/exhibitor/home/':  ('cks-banner-left.png', 'cks-banner-dancers-01.png',),
        '/retailer/home/':   ('cks-banner-left.png', 'cks-banner-dancers-01.png',),

        '/register/':        ('cks-banner-left.png', 'cks-banner-handstand-01.png',),
        '/checkout/':        ('cks-banner-left.png', 'cks-banner-handstand-01.png',),
        '/registered/':      ('cks-banner-left.png', 'cks-banner-handstand-01.png',),

        '/invoices/':        ('cks-banner-left.png', 'cks-banner-poodle-01.png',),
        '/invoice/':         ('cks-banner-left.png', 'cks-banner-poodle-01.png',),
        '/registrations/':   ('cks-banner-left.png', 'cks-banner-poodle-01.png',),

        '/lines/':           ('cks-banner-left.png', 'cks-banner-yellow-01.png',),

        '/edit/':            ('cks-banner-left.png', 'cks-banner-dino1-01.png',),

        '/report/':          ('cks-banner-left.png', 'cks-banner-camera-01.png',),

        '/exhibitors/':      ('cks-banner-left.png', 'cks-banner-snowhat-01.png',),
    },
}

def _get_banner(path, venue):
    if   path.startswith('/accounts/'):   path = '/accounts/'
    elif path.startswith('/advising/'):   path = '/advising/'
    elif path.startswith('/invoice/'):    path = '/invoice/'
    elif path.startswith('/checkout/'):   path = '/checkout/'
    elif path.startswith('/registered/'): path = '/registered/'
    elif path.startswith('/report/'):     path = '/report/'
    elif path.startswith('/exhibitors/'): path = '/exhibitors/'
    try:
        return banner_map[venue][path]
    except KeyError:
        logger.error('could not find a banner mapping for path %s' % path)
    if venue == 'cakidsshow':
        return CKS_DEFAULT_BANNER
    return NWKS_DEFAULT_BANNER

def banner_context(request):
    venue = _get_venue(request)
    banner_left, banner_right = _get_banner(request.path, venue)
    return {
        'banner_left':  banner_left,
        'banner_right': banner_right,
    }

# make sure this exhibitor has the right to see the retailers for this show:
# that they registered for it
# is meant to throw ObjectDoesNotExist when fails
def _fetch_exhibitor(user, show_id=None):
    exhibitor = Exhibitor.objects.get(user=user)
    show = Show.objects.get(id=show_id) if show_id else None
    registration = Registration.objects.get(show=show, exhibitor=exhibitor) if show_id else None
    return exhibitor, show, registration

def _fetch_exhibitor_id(exhibitor_id, show_id=None):
    exhibitor = Exhibitor.objects.get(id=exhibitor_id)
    show = Show.objects.get(id=show_id) if show_id else None
    registration = Registration.objects.get(show=show, exhibitor=exhibitor) if show_id else None
    return exhibitor, show, registration

# make sure this retailer has the right to see the exhibitors for this show:
# that they registered for it
# is meant to throw ObjectDoesNotExist when fails
def _fetch_retailer(user, show_id=None):
    retailer = Retailer.objects.get(user=user)
    show = Show.objects.get(id=show_id) if show_id else None
    registration = RetailerRegistration.objects.get(show=show, retailer=retailer) if show_id else None
    return retailer, show, registration

def _get_rooms(show):
    rooms = {}
    registrations = Registration.objects.filter(show=show)
    for r in registrations:
        rooms[r.exhibitor.id] = r.room
    return rooms

### views ###

def home(request):
    venue = _get_venue(request)
    # pprint(timezone.localtime(timezone.now(), Pacific_tzinfo()))
    # pprint(timezone.localtime(timezone.now(), Pacific_tzinfo()).date())
    # show = Show.objects.filter(end_date__gt=datetime.date.today()).latest('end_date')
    show = Show.objects.filter(venue=venue, end_date__gte=timezone.localtime(timezone.now(), pacific_tzinfo).date()).latest('end_date')
    # TODO this still assumes only one active show at a time ever.
    return render_to_response('home.html',
                              {'show': show, },
                              context_instance=RequestContext(request))

def contact(request):
    return render_to_response('contact.html', {}, context_instance=RequestContext(request))

def about(request):
    return render_to_response('about.html', {}, context_instance=RequestContext(request))

def privacy_policy(request):
    return render_to_response('privacy_policy.html', {}, context_instance=RequestContext(request))

def make_500(request):
    raise ObjectDoesNotExist()

@login_required(login_url='/advising/login/')
@user_passes_test(user_is_exhibitor_or_retailer, login_url='/advising/denied/')
def password_change_wrapper(request, template_name, post_change_redirect):
    """
    I want to use the built-in password_change() view from django
    but I also want to clear the must_change_password flag only when
    the Retailer or Exhibitor has successfully changed their password.
    See also: nwkidsshow.middleware.ForcePasswordChange where I implement
    a middleware process_view() to redirect all requests to /accounts/password_change
    whenever the must_change_password is set.
    """
    user = get_user(request)
    # print(user.must_change_password)
    check_return = password_change(request,
                                   template_name=template_name,
                                   post_change_redirect=post_change_redirect)
    # pprint(check_return)
    if isinstance(check_return, HttpResponseRedirect):
        # Password changed successfully so
        # clear the flag that forces user to change password
        if (user):
            user.must_change_password = False
            user.save()
    return check_return

def profile(request):
    # somebody just logged in successfully
    # based on what group they're in, redirect them appropriately
    # exhibitors --> exhibitor page
    # retailers --> retailer page
    # neither --> admin portal??

    # this might be moot, since deactivated users can't even
    # log in and won't get to this point!
    if not request.user.is_active:
        return redirect('/advising/deactivated/')

    if user_is_exhibitor(request.user):
        return redirect('/exhibitor/home/')
    elif user_is_retailer(request.user):
        return redirect('/retailer/home/')
    elif request.user.is_staff:
        return redirect('/admin/')
    # TODO log an error, this should not happen, they logged in after all!
    return redirect('/')


@login_required(login_url='/advising/login/')
@user_passes_test(user_is_exhibitor, login_url='/advising/denied/')
def exhibitor_home(request):
    return render_to_response('exhibitor.html', {}, context_instance=RequestContext(request))

@login_required(login_url='/advising/login/')
@user_passes_test(user_is_retailer, login_url='/advising/denied/')
def retailer_home(request):
    return render_to_response('retailer.html', {}, context_instance=RequestContext(request))


def get_better_choices(shows, show_count):
    # SPECIAL: I am too lazy to AJAX back for the actual dates on the checkboxes.
    # BUT there is usually only ONE show to register for at a time, so grab those
    # dates, as strings, and pass to the form as better "choices"
    choices = []
    if show_count == 1:
        show = shows[0]
        delta = (show.end_date - show.start_date).days
        for d in range(0, delta+1, 1):
            dateObject = show.start_date + datetime.timedelta(days=d)
            dateString = dateObject.strftime("%A, %B %d") # Thursday, October 24
            # choices.append((d+1, dateString))
            choices.append((d, dateString))
    # print 'CHOICES'
    # pprint(choices)
    return choices


def get_initial_retailer_registration(retailer, shows, show_count):
    if not show_count:
        return {}
    try:
        registration = RetailerRegistration.objects.get(show=shows[0], retailer=retailer)
    except ObjectDoesNotExist:
        return {}
    # pprint(model_to_dict(registration))
    return model_to_dict(registration)

def get_initial_exhibitor_registration(exhibitor, shows, show_count):
    if not show_count:
        return {}
    try:
        registration = Registration.objects.get(show=shows[0], exhibitor=exhibitor)
    except ObjectDoesNotExist:
        return {}
    # pprint(model_to_dict(registration))
    return model_to_dict(registration)

@login_required(login_url='/advising/login/')
@user_passes_test(user_is_exhibitor_or_retailer, login_url='/advising/denied/')
def register(request):
    venue = _get_venue(request)
    today = timezone.localtime(timezone.now(), pacific_tzinfo).date()
    retailer = None
    exhibitor = None
    form = None

    if user_is_exhibitor(request.user):
        exhibitor = Exhibitor.objects.get(user=request.user)
        shows = Show.objects.filter(Q(venue=venue) & Q(closed_date__gte=today) & ~Q(exhibitors=exhibitor))
    else: # retailer
        retailer = Retailer.objects.get(user=request.user)
        shows = Show.objects.filter(venue=venue,
                                    end_date__gte=today)
    show_count = shows.count()

    if request.method != 'POST': # a GET

        if user_is_retailer(request.user):
            form = RetailerRegistrationForm(
                show=shows,
                initial=get_initial_retailer_registration(retailer, shows, show_count),
                better_choices=get_better_choices(shows, show_count)
            )

        if user_is_exhibitor(request.user):
            form = ExhibitorRegistrationForm(
                show=shows,
                initial=get_initial_exhibitor_registration(exhibitor, shows, show_count)
            )

    else: # a POST

        if user_is_exhibitor(request.user):
            form = ExhibitorRegistrationForm(request.POST, show=shows)
            if form.is_valid():
                cd = form.cleaned_data

                # grab some fields form the form
                show           = cd['show']
                num_associates = cd['num_associates']
                num_assistants = cd['num_assistants'] or 0
                num_racks      = cd['num_racks'] or 0
                num_tables     = cd['num_tables'] or 0

                # is_late        = cd['show'].late_date < datetime.date.today()
                late_date = cd['show'].late_date
                late_datetime_aware = datetime.datetime(late_date.year, late_date.month, late_date.day,
                                                        hour=23, minute=59, second=59, tzinfo=pacific_tzinfo)
                now_datetime_aware = timezone.localtime(timezone.now(), pacific_tzinfo)
                # print(late_datetime_aware)
                # pprint(late_datetime_aware)
                # print(now_datetime_aware)
                # pprint(now_datetime_aware)
                is_late = late_datetime_aware < now_datetime_aware

                # compute the individual charges...
                registration_total = cd['show'].registration_fee
                assistant_total    = cd['show'].assistant_fee * num_assistants
                rack_total         = cd['show'].rack_fee * num_racks
                late_total         = cd['show'].late_fee if is_late else 0.0

                # ... and the final total
                total = registration_total + \
                        assistant_total + \
                        rack_total + \
                        late_total

                # store in the object for display on the next page !!! not if you fix this !!!
                # TODO: can I remove this now?
                cd['registration_total'] = registration_total
                cd['assistant_total']    = assistant_total
                cd['rack_total']         = rack_total
                cd['late_total']         = late_total
                cd['total']              = total

                # Add this exhibitor to the Show exhibitors
                show.exhibitors.add(exhibitor)

                # add a new registration object and associate with this exhibitor & show
                # TODO change this and all others like this to use get_or_create()  obj, created = Person.objects.get_or_create(first_name='John', last_name='Lennon', defaults={'birthday': date(1940, 10, 9)})
                try:
                    r = Registration.objects.get(exhibitor=exhibitor, show=show)
                    # print "Registration for (%s & %s) already exists" % (exhibitor.user, show.name)
                except ObjectDoesNotExist:
                    r = Registration(exhibitor=exhibitor, show=show)
                    r.has_paid = False
                    # print "created registration: (%s & %s)" % (exhibitor.user, show.name)
                r.num_exhibitors     = num_associates
                r.num_assistants     = num_assistants
                r.num_racks          = num_racks
                r.num_tables         = num_tables
                r.is_late            = is_late
                # r.date_registered    = datetime.date.today()
                r.date_registered    = today
                r.registration_total = registration_total
                r.assistant_total    = assistant_total
                r.rack_total         = rack_total
                r.late_total         = late_total
                r.total              = total
                r.save()

                # display the show info, fees, disclaimers, etc. on a nice page
                return redirect('/invoice/%s/' % show.id)
        else:
            # print "### found retailer %s" % retailer.user
            form = RetailerRegistrationForm(request.POST, show=shows, better_choices=get_better_choices(shows, show_count))
            if form.is_valid():
                cd = form.cleaned_data
                # pprint(cd)

                # grab some fields form the form
                show           = cd['show']
                num_attendees  = cd['num_attendees']
                days_attending = cd['days_attending'] # gives you: [u'0', u'1']
                # days_attending = [eval(x) for x in days_attending] # gives you: [0, 1]
                # days_attending = [unicode(x) for x in days_attending] # gives you: [u'0', u'1']
                days_attending = ','.join(days_attending) # gives you: u'0,1', suitable for the stupid CommaSeparatedIntegerField

                # Add this exhibitor to the Show exhibitors
                show.retailers.add(retailer)

                # add a new registration object and associate with this retailer & show
                # TODO change this and all others like this to use get_or_create()  obj, created = Person.objects.get_or_create(first_name='John', last_name='Lennon', defaults={'birthday': date(1940, 10, 9)})
                try:
                    r = RetailerRegistration.objects.get(retailer=retailer, show=show)
                    # print "RetailerRegistration for (%s & %s) already exists" % (retailer.user, show.name)
                except ObjectDoesNotExist:
                    r = RetailerRegistration(retailer=retailer, show=show)
                    # print "created RetailerRegistration: (%s & %s)" % (retailer.user, show.name)
                r.num_attendees  = num_attendees
                r.days_attending = days_attending
                r.save()

                # TODO: convert days attending to actual dates and show on the "registered" page.
                return redirect('/registered/%s/' % show.id)

    return render_to_response('register.html',
                              {'form': form,
                               'show_count': show_count,
                               'is_exhibitor': user_is_exhibitor(request.user)},
                              context_instance=RequestContext(request))

@login_required(login_url='/advising/login/')
@user_passes_test(user_is_exhibitor, login_url='/advising/denied/')
def checkout(request, show_id):
    venue = _get_venue(request)

    try:
        exhibitor, show, registration = _fetch_exhibitor(request.user, show_id=show_id)
    except ObjectDoesNotExist:
        return redirect('/advising/noinvoice/')

    if registration.has_paid:
        logger.error('Exhibitor %s %s is checking out when has already paid for show %s %s' %
                     (exhibitor.first_name_display(), exhibitor.last_name_display(), venue, show.name))

    amount = '%.2f' % registration.total

    if request.method != 'POST': # a GET
        form = CheckoutForm()
    else:
        form = CheckoutForm(request.POST)
        if form.is_valid():
            cd = form.cleaned_data

            # pprint(cd)
            name   = cd['cardholder_name']
            number = cd['number']
            month  = cd['month']
            year   = cd['year']

            # do some validation on the fields? integers, lengths, etc....?
            # No, braintree does all of that - I just need to convey the error message.

            dynamic_descriptor = 'Laurel Event*nwkidshow'
            if venue == 'cakidsshow':
                dynamic_descriptor = 'Laurel Event*cakidshow'

            transaction = {
                "amount": amount,
                "credit_card": {
                    "cardholder_name": name,
                    "number": number,
                    "expiration_month": month,
                    "expiration_year": year,
                },
                "options": {
                    "submit_for_settlement": True,
                },
                "customer": {
                    "first_name": exhibitor.first_name_display(),
                    "last_name": exhibitor.last_name_display(),
                    "company": exhibitor.company,
                    "phone": exhibitor.phone,
                    "fax": exhibitor.fax,
                    "website": exhibitor.website,
                    "email": exhibitor.email_display(),
                },
                "descriptor": {
                    "name": dynamic_descriptor,
                    "phone": "503-330-7167",
                }
            }

            if running_in_prod:
                if venue == 'cakidsshow':
                    transaction['merchant_account_id'] = 'LaurelEventCAKidsShow_instant'
                # else nothing - defaults to NW Kids Show.
            else:
                transaction['merchant_account_id'] = '26f63sqbcy4hfn55'

            if not running_in_prod:
                pprint(transaction)

            result = braintree.Transaction.sale(transaction)

            if not running_in_prod:
                pprint(result)

            if result.is_success:
                logger.error('%s %s (cardholder %s) successfully charged %s on %s' %
                             (exhibitor.first_name_display(), exhibitor.last_name_display(),
                              name, amount, result.transaction.credit_card['last_4']))

                # update the database has_paid and details of the transaction for the receipt
                registration.has_paid = True
                registration.save()

                # show them the receipt with relevant details (which they can print)
                return render_to_response('receipt.html',
                                          {
                                              'transaction': result.transaction,
                                          },
                                          context_instance=RequestContext(request))
            else:
                status = result.transaction
                status = status and result.transaction.status
                if status == 'processor_declined':
                    code = result.transaction.processor_response_code
                    message1 = 'The payment processor declined the credit card transaction.'
                    message2 = result.transaction.processor_response_text
                elif status == 'gateway_rejected':
                    code = 'n/a'
                    message1 = 'The payment gateway rejected the credit card transaction.'
                    message2 = result.transaction.gateway_rejection_reason
                else:
                    code = 'n/a'
                    #code = ???? result.errors.deep_errors[0].code
                    message1 = 'There was a problem processing this credit card transaction'
                    message2 = result.message
                logger.error('%s %s (cardholder %s) failed to charge %s: %s: %s' %
                             (exhibitor.first_name_display(), exhibitor.last_name_display(),
                              name, amount, status, message2))
                return render_to_response('checkout_error.html',
                              {
                                  'message1': message1,
                                  'message2': message2,
                                  'show': show,
                              },
                              context_instance=RequestContext(request))
                # result.message
    return render_to_response('checkout.html',
                              {
                                  'form': form,
                                  'amount': amount,
                              },
                              context_instance=RequestContext(request))

@login_required(login_url='/advising/login/')
@user_passes_test(user_is_retailer, login_url='/advising/denied/')
def registrations(request):
    venue = _get_venue(request)
    retailer = Retailer.objects.get(user=request.user)
    regs = RetailerRegistration.objects.filter(show__venue=venue, retailer=retailer)
    return render_to_response('registrations.html', {'registrations': regs},
                              context_instance=RequestContext(request))

@login_required(login_url='/advising/login/')
@user_passes_test(user_is_retailer, login_url='/advising/denied/')
def registered(request, show_id):
    try:
        retailer, show, registration = _fetch_retailer(request.user, show_id=show_id)
    except ObjectDoesNotExist:
        return redirect('/advising/noregistration/')
    return render_to_response('registered.html',
                              {
                                  'show': show,
                                  'registration': registration
                              },
                              context_instance=RequestContext(request))

@login_required(login_url='/advising/login/')
@user_passes_test(user_is_exhibitor, login_url='/advising/denied/')
def invoices(request):
    venue = _get_venue(request)
    exhibitor = Exhibitor.objects.get(user=request.user)
    # print "### found exhibitor %s" % exhibitor.user
    invoices = Registration.objects.filter(show__venue=venue, exhibitor=exhibitor)
    return render_to_response('invoices.html', {'invoices': invoices},
                              context_instance=RequestContext(request))

@login_required(login_url='/advising/login/')
@user_passes_test(user_is_exhibitor, login_url='/advising/denied/')
def invoice(request, show_id):
    try:
        exhibitor, show, registration = _fetch_exhibitor(request.user, show_id=show_id)
    except ObjectDoesNotExist:
        return redirect('/advising/noinvoice/')
    return render_to_response('invoice.html',
                              {
                                  'show': show,
                                  'registration': registration
                              },
                              context_instance=RequestContext(request))

@login_required(login_url='/advising/login/')
@user_passes_test(user_is_exhibitor, login_url='/advising/denied/')
def lines(request):
    exhibitor = Exhibitor.objects.get(user=request.user)
    lines_str = exhibitor.lines # 'aline1 * aline 2 * aline 3'
    # pprint(lines_str)
    lines_list = lines_str.split(' * ') # ['aline1','aline2','aline3']
    # pprint(lines_list)
    num_lines = len(lines_list)
    lines_dict = {} # {'line_1':'aline1', 'line_2':'aline2', 'line_3':'aline3' }
    for i in xrange(1, num_lines + 1):
        lines_dict['line_%i' % i] = lines_list[i-1]
    # pprint(lines_dict)
    if request.method != 'POST': # a GET
        form = ExhibitorLinesForm(num_lines=num_lines, initial=lines_dict)
    else:
        form = ExhibitorLinesForm(request.POST, num_lines=num_lines)
        if form.is_valid():
            lines_dict = form.cleaned_data # {'line_1': u'aline1', 'line_2': u'aline2', 'line_3': u'aline3'}
            # pprint(lines_dict)
            # grab some fields form the form
            # build it back into my ' * ' delimited format
            lines_list = []
            for key in sorted(lines_dict.iterkeys()):
                if lines_dict[key]:
                    lines_list.append(lines_dict[key])
                else:
                    del lines_dict[key]
            # pprint(lines_list)
            lines_str = ' * '.join(lines_list)
            # pprint(lines_str)
            # and store it back to the database
            exhibitor.lines = lines_str
            exhibitor.save()
            if 'save' in request.POST:
                return redirect('/lines/')
            elif 'done' in request.POST:
                return redirect('/exhibitor/home/')

    return render_to_response('lines.html', {'form': form}, context_instance=RequestContext(request))

@login_required(login_url='/advising/login/')
@user_passes_test(user_is_exhibitor_or_retailer, login_url='/advising/denied/')
def edit(request):
    form = None
    user = User.objects.get(username=request.user.username)
    # pprint(user)
    if user_is_retailer(request.user):
        retailer = Retailer.objects.get(user=request.user)
        if request.method != 'POST': # a GET
            form = RetailerForm(instance=retailer, initial=model_to_dict(user))
        else: # a POST
            form = RetailerForm(request.POST, instance=retailer)
            if form.is_valid():
                form.save()
                cd = form.cleaned_data
                user.first_name = cd['first_name']
                user.last_name  = cd['last_name']
                user.email      = cd['email']
                user.save()
                return redirect('/retailer/home/')
    else:
        exhibitor = Exhibitor.objects.get(user=request.user)
        if request.method != 'POST': # a GET
            form = ExhibitorForm(instance=exhibitor, initial=model_to_dict(user))
        else: # a POST
            form = ExhibitorForm(request.POST, instance=exhibitor)
            if form.is_valid():
                form.save()
                cd = form.cleaned_data
                user.first_name = cd['first_name']
                user.last_name  = cd['last_name']
                user.email      = cd['email']
                user.save()
                return redirect('/exhibitor/home/')
    return render_to_response('edit.html',
                              {'form': form,},
                              context_instance=RequestContext(request))


@login_required(login_url='/advising/login/')
@user_passes_test(user_is_exhibitor, login_url='/advising/denied/')
def report_retailers_form(request):
    venue = _get_venue(request)
    # Have the exhibitor choose which show to report on.
    # Only let them choose from shows they have registered for.
    exhibitor = Exhibitor.objects.get(user=request.user)
    shows = Show.objects.filter(venue=venue, exhibitors=exhibitor)
    show_count = shows.count()
    show_latest_id = None
    if show_count:
        show_latest = shows.latest('end_date')
        show_latest_id = show_latest.id
    if request.method != 'POST': # a GET
        form = RetailerReportForm(shows=shows, exhibitor=exhibitor, initial={'show': show_latest_id})
    else: # a POST
        form = RetailerReportForm(request.POST, shows=shows, exhibitor=exhibitor,  initial={'show': show_latest_id})
        if form.is_valid():
            cd = form.cleaned_data
            # pprint(cd)
            show = cd['show']
            return redirect('/report/retailers/%s/' % show.id)
    return render_to_response('report_retailers_form.html',
                              {'form': form,
                               'show_count': show_count,},
                              context_instance=RequestContext(request))

@login_required(login_url='/advising/login/')
@user_passes_test(user_is_exhibitor, login_url='/advising/denied/')
def report_retailers(request, show_id):
    try:
        exhibitor, show, registration = _fetch_exhibitor(request.user, show_id=show_id)
        retailers = Retailer.objects.filter(show=show).exclude(user__first_name='Test').order_by('user__last_name')
    except ObjectDoesNotExist:
        return redirect('/advising/noregistration/')
    return render_to_response('report_retailers.html',
                              {
                                  'retailers': retailers,
                                  'show': show,
                              },
                              context_instance=RequestContext(request))


@login_required(login_url='/advising/login/')
@user_passes_test(user_is_exhibitor, login_url='/advising/denied/')
def report_retailers_xls(request, show_id):
    try:
        exhibitor, show, registration = _fetch_exhibitor(request.user, show_id=show_id)
        retailers = Retailer.objects.filter(show=show).exclude(user__first_name='Test').order_by('user__last_name')
    except ObjectDoesNotExist:
        return redirect('/advising/noregistration/')
    fields = ['company',
              'website',
              'address',
              'address2',
              'city',
              'state',
              'zip',
              'phone',
              'fax',
              ]

    retailers_list = []
    for retailer in retailers:
        e = model_to_dict(retailer, fields=fields)
        t = ()
        t = t + (retailer.first_name_display(),)
        t = t + (retailer.last_name_display(),)
        t = t + (retailer.email_display(),)
        for f in fields:
            t = t + (e[f],)
        retailers_list += [t]

    http_response = HttpResponse(mimetype='application/vnd.ms-excel')
    http_response['Content-Transfer-Encoding'] = 'Binary'
    http_response['Content-disposition'] = 'attachment; filename="nwkidsshow_retailers.xls"'

    retailer_xls(retailers_list, http_response)
    return http_response


@login_required(login_url='/advising/login/')
@user_passes_test(user_is_retailer, login_url='/advising/denied/')
def report_exhibitors_form(request):
    venue = _get_venue(request)
    # Have the retailer choose which show to report on.
    # Only let them choose from shows they have registered for.
    retailer = Retailer.objects.get(user=request.user)
    shows = Show.objects.filter(venue=venue, retailers=retailer)
    show_count = shows.count()
    show_latest_id = None
    if show_count:
        show_latest = shows.latest('end_date')
        show_latest_id = show_latest.id
    if request.path == u'/report/exhibitors/':
        title = u'List Exhibitors Registered for a Show'
    else:
        title = u"List Exhibitors' Lines at a Show"
    if request.method != 'POST': # a GET
        form = ExhibitorReportForm(shows=shows, retailer=retailer, initial={'show': show_latest_id})
    else: # a POST
        form = ExhibitorReportForm(request.POST, shows=shows, retailer=retailer,  initial={'show': show_latest_id})
        if form.is_valid():
            cd = form.cleaned_data
            show = cd['show']
            # pprint(request.path)
            if request.path == u'/report/exhibitors/':
                return redirect('/report/exhibitors/%s/' % show.id)
            else:
                return redirect('/report/lines/%s/' % show.id)
    return render_to_response('report_exhibitors_form.html',
                              {'form': form,
                               'show_count': show_count,
                               'title': title, },
                              context_instance=RequestContext(request))



@login_required(login_url='/advising/login/')
@user_passes_test(user_is_retailer, login_url='/advising/denied/')
def report_exhibitors(request, show_id):
    try:
        retailer, show, registration = _fetch_retailer(request.user, show_id=show_id)
        exhibitors = Exhibitor.objects.filter(show=show).exclude(user__first_name='Test').order_by('user__last_name')
    except ObjectDoesNotExist:
        return redirect('/advising/noregistration/')
    rooms = _get_rooms(show)
    return render_to_response('report_exhibitors.html',
                              {
                                  'exhibitors': exhibitors,
                                  'show': show,
                                  'rooms': rooms,
                               },
                              context_instance=RequestContext(request))


@login_required(login_url='/advising/login/')
@user_passes_test(user_is_retailer, login_url='/advising/denied/')
def report_exhibitors_xls(request, show_id):
    try:
        retailer, show, registration = _fetch_retailer(request.user, show_id=show_id)
        exhibitors = Exhibitor.objects.filter(show=show).exclude(user__first_name='Test').order_by('user__last_name')
    except ObjectDoesNotExist:
        return redirect('/advising/noregistration/')
    rooms = _get_rooms(show)

    fields = ['company',
              'website',
              'address',
              'address2',
              'city',
              'state',
              'zip',
              'phone',
              'fax',
              'lines',
              ]

    exhibitors_list = []
    for exhibitor in exhibitors:
        e = model_to_dict(exhibitor, fields=fields)
        t = ()
        t = t + (rooms[exhibitor.id],)
        t = t + (exhibitor.first_name_display(),)
        t = t + (exhibitor.last_name_display(),)
        t = t + (exhibitor.email_display(),)
        for f in fields:
            t = t + (e[f],)
        exhibitors_list += [t]

    http_response = HttpResponse(mimetype='application/vnd.ms-excel')
    http_response['Content-Transfer-Encoding'] = 'Binary'
    http_response['Content-disposition'] = 'attachment; filename="nwkidsshow_exhibitors.xls"'

    exhibitor_xls(exhibitors_list, http_response)
    return http_response

# return a sorted list of tuples [(line, name, id, room#), ... ]
def _build_lines_data(show):
    rooms = _get_rooms(show)
    exhibitors = Exhibitor.objects.filter(show=show).exclude(user__first_name='Test')

    lines_list2 = []
    for exhibitor in exhibitors:
        exhibitor_name = '%s %s' % (exhibitor.first_name_display(),exhibitor.last_name_display())
        lines_str = exhibitor.lines  # 'aline1 * aline 2 * aline 3'
        # pprint(lines_str)
        lines_list = lines_str.split(' * ')  # ['aline1','aline2','aline3']
        # pprint(lines_list)
        for line in lines_list:
            stripped_line = line.strip()
            if stripped_line:
                lines_list2 += [(stripped_line, exhibitor_name, exhibitor.id, rooms[exhibitor.id]),]
    # pprint(lines_list2)
    # case insensitive sort by the line name
    lines_list = sorted(lines_list2, key=lambda t: tuple(t[0].lower()))
    # pprint(lines_list)
    return lines_list


@login_required(login_url='/advising/login/')
@user_passes_test(user_is_retailer, login_url='/advising/denied/')
def report_lines(request, show_id):
    try:
        retailer, show, registration = _fetch_retailer(request.user, show_id)
    except ObjectDoesNotExist:
        return redirect('/advising/noregistration/')
    lines_list = _build_lines_data(show)
    return render_to_response('report_lines.html',
                              {
                                  'show': show,
                                  'lines': lines_list,
                              },
                              context_instance=RequestContext(request))

@login_required(login_url='/advising/login/')
@user_passes_test(user_is_retailer, login_url='/advising/denied/')
def report_lines_xls(request, show_id):
    try:
        retailer, show, registration = _fetch_retailer(request.user, show_id)
    except ObjectDoesNotExist:
        return redirect('/advising/noregistration/')
    lines_list = _build_lines_data(show)
    lines_list = [(a,b,c) for a,b,x,c in lines_list]  # don't need the id

    http_response = HttpResponse(mimetype='application/vnd.ms-excel')
    http_response['Content-Transfer-Encoding'] = 'Binary'
    http_response['Content-disposition'] = 'attachment; filename="nwkidsshow_exhibitors_lines.xls"'

    exhibitor_lines_xls(lines_list, http_response)
    return http_response

@login_required(login_url='/advising/login/')
@user_passes_test(user_is_retailer, login_url='/advising/denied/')
def exhibitor(request, exhibitor_id, show_id):
    # make sure this retailer and exhibitor (they want to see) have BOTH registered for this show!
    try:
        retailer,  show, registration = _fetch_retailer(request.user, show_id=show_id)
        exhibitor, show, registration = _fetch_exhibitor_id(exhibitor_id, show_id=show_id)
    except ObjectDoesNotExist:
        return redirect('/advising/not_allowed_exhibitor/')
    return render_to_response('exhibitor_info.html',
                              {
                                  'e': exhibitor,
                                  'room': registration.room,
                              },
                              context_instance=RequestContext(request))


@staff_member_required
def add_user(request):
    if request.method != 'POST': # a GET
        form = AddUserForm()
    else: # a POST
        form = AddUserForm(request.POST)
        if form.is_valid():
            cd = form.cleaned_data
            # see clean_username in AddUserForm for where I make sure it does not exist yet
            u = User.objects.create_user(username=cd['username'])
            u.first_name = cd['first_name']
            u.last_name  = cd['last_name']
            u.email      = cd['email']
            u.set_password(cd['password'])
            u.save()
            if cd['attendee_type'] == 'exhibitor':
                e = Exhibitor(user=u)
                e.must_change_password = True
                e.save()
                # print "creating exhibitor %s" % e
                group = Group.objects.get(name='exhibitor_group')
            else:
                r = Retailer(user=u)
                r.must_change_password = True
                r.save()
                # print "creating retailer %s" % r
                group = Group.objects.get(name='retailer_group')
            u.groups.add(group)
            venues = cd['venues'] # gives you: [u'cks', u'nwks'] or one or none in the list
            if 'cks' in venues:
                group = Group.objects.get(name='cakidsshow_group')
                u.groups.add(group)
            if 'nwks' in venues:
                group = Group.objects.get(name='nwkidsshow_group')
                u.groups.add(group)
            return redirect('/add-user/')
    return render_to_response('add_user.html',
                              {
                                  'form': form,
                              },
                              context_instance=RequestContext(request))

@staff_member_required
def dump(request):
    users      = User.objects.all()
    exhibitors = Exhibitor.objects.all()
    retailers  = Retailer.objects.all()
    shows      = Show.objects.all()
    exhibitor_registrations = Registration.objects.all()
    retailer_registrations  = RetailerRegistration.objects.all()
    return render_to_response('dump.html', {
                                            'users'      : users,
                                            'exhibitors' : exhibitors,
                                            'retailers'  : retailers,
                                            'shows'      : shows,
                                            'exh_regs'   : exhibitor_registrations,
                                            'ret_regs'   : retailer_registrations,
                                            },
                              context_instance=RequestContext(request))

def populate_users(users, group):
    for user in users:
        try:
            u = User.objects.get(username=user['username'])
            # print "user already exists: %s (%s)" % (u.username, u.get_full_name())
        except ObjectDoesNotExist:
            u = User.objects.create_user(username=user['username'])
            # print "created user: %s" % u.username
        u.first_name = user['first_name'] if not u.first_name else u.first_name
        u.last_name  = user['last_name']  if not u.last_name else u.last_name
        u.email      = user['email']      if not u.email else u.email
        if not u.password or not u.has_usable_password():
            u.set_password(user['password'])
            # print 'set %s password to %s' % (u.get_full_name(), user['password'])
        else:
            pass
            # print 'password for %s is %s' % (u.get_full_name(), u.password)
        u.save()
        u.groups.add(group)
    return


def populate_exhibitors(exhibitors):
    for exhibitor in exhibitors:
        user = User.objects.get(username=exhibitor['username']) # had better be one already!
        try:
            e = Exhibitor.objects.get(user=user)
            # print "updating exhibitor %s" % e
        except ObjectDoesNotExist:
            e = Exhibitor(user=user)
            # print "creating exhibitor %s" % e
        e.company   = exhibitor['company']  if not e.company  else e.company
        e.website   = exhibitor['website']  if not e.website  else e.website
        e.address   = exhibitor['address']  if not e.address  else e.address
        e.address2  = exhibitor['address2'] if not e.address2 else e.address2
        e.city      = exhibitor['city']     if not e.city     else e.city
        e.state     = exhibitor['state']    if not e.state    else e.state
        e.phone     = exhibitor['phone']    if not e.phone    else e.phone
        e.zip       = exhibitor['zip']      if not e.zip      else e.zip
        e.fax       = exhibitor['fax']      if not e.fax      else e.fax
        e.lines     = exhibitor['lines']    if not e.lines    else e.lines
        e.must_change_password = True # False
        e.save()
    return


def populate_retailers(retailers):
    for retailer in retailers:
        user = User.objects.get(username=retailer['username']) # had better be one already!
        try:
            r = Retailer.objects.get(user=user)
            # print "updating retailer %s" % r
        except ObjectDoesNotExist:
            r = Retailer(user=user)
            # print "creating retailer %s" % r
        r.company   = retailer['company']  if not r.company  else r.company
        r.website   = retailer['website']  if not r.website  else r.website
        r.address   = retailer['address']  if not r.address  else r.address
        r.address2  = retailer['address2'] if not r.address2 else r.address2
        r.city      = retailer['city']     if not r.city     else r.city
        r.state     = retailer['state']    if not r.state    else r.state
        r.phone     = retailer['phone']    if not r.phone    else r.phone
        r.zip       = retailer['zip']      if not r.zip      else r.zip
        r.fax       = retailer['fax']      if not r.fax      else r.fax
        r.must_change_password = True # False
        r.save()
    return


def register_exhibitor(e,s):
    try:
        reg = Registration.objects.get(exhibitor=e, show=s)
        # print "Exhibitor Registration for %s to %s already exists" % (e,s)
    except ObjectDoesNotExist:
        reg = Registration(exhibitor=e, show=s)
        # print "Exhibitor Registration created for %s to %s" % (e,s)
        reg.num_exhibitors = 0
        reg.num_assistants = 0
        reg.num_racks = 0
        reg.num_tables = 0
        reg.is_late = False
        # reg.date_registered = datetime.date.today()
        reg.date_registered = timezone.localtime(timezone.now(), pacific_tzinfo).date()
        reg.registration_total = 0
        reg.assistant_total = 0
        reg.rack_total = 0
        reg.late_total = 0
        reg.total = 0
        reg.has_paid = True
        reg.save()

def register_retailer(r,s):
    try:
        reg = RetailerRegistration.objects.get(retailer=r, show=s)
        # print "Retailer Registration for %s to %s already exists" % (r,s)
    except ObjectDoesNotExist:
        reg = RetailerRegistration(retailer=r, show=s)
        # print "Retailer Registration created for %s to %s" % (r,s)
        reg.num_attendees = 0
        reg.days_attending = "0"
        reg.save()


def populate_shows(shows):
    #Show.objects.all().delete()
    for show in shows:
        try:
            s = Show.objects.get(name=show['name'], venue=show['venue'])
            # print "updating show %s" % s
        except ObjectDoesNotExist:
            s = Show(name=show['name'], venue=show['venue'])
            # print "creating show %s" % s
        s.late_date   = show['late_date']   if not s.late_date   else s.late_date
        s.closed_date = show['closed_date'] if not s.closed_date else s.closed_date
        s.start_date  = show['start_date']  if not s.start_date  else s.start_date
        s.end_date    = show['end_date']    if not s.end_date    else s.end_date
        s.registration_fee = show['registration_fee']
        s.assistant_fee    = show['assistant_fee']
        s.late_fee         = show['late_fee']
        s.rack_fee         = show['rack_fee']
        # must save before add manytomany!
        s.save()

        if show['name'] == 'February 2013':
            for exhibitor in Exhibitor.objects.all():
                s.exhibitors.add(exhibitor)
                register_exhibitor(exhibitor, s)
            for retailer in Retailer.objects.all():
                s.retailers.add(retailer)
                register_retailer(retailer, s)

import retailer_data
import exhibitor_data
import show_data

def all_users_to_groups():
    # add all retailers and exhibitors ot the new nwkidsshow group
    group,created = Group.objects.get_or_create(name='nwkidsshow_group')
    users = User.objects.all()
    for user in users:
        user.groups.add(group)

    # add all Exhibitors to the new cakidsshow group (not retailers!)
    group,created = Group.objects.get_or_create(name='cakidsshow_group')
    exhibitors = User.objects.all()
    for user in users:
        if user.groups.filter(name='exhibitor_group').exists():
            user.groups.add(group)


@staff_member_required
def seed(request):

    # all_users_to_groups()

    populate_shows(show_data.shows)

    # TURNING THIS OFF NOW
    return HttpResponseRedirect('/dump/')

    exhibitor_group, created = Group.objects.get_or_create(name='exhibitor_group')
    # if created:
    #     print "created new exhibitor_group"
    # else:
    #     print "exhibitor_group already exists"
    retailer_group,  created = Group.objects.get_or_create(name='retailer_group')
    # if created:
    #     print "created new retailer_group"
    # else:
    #     print "retailer_group already exists"

    populate_users(exhibitor_data.exhibitors, exhibitor_group)
    populate_users(retailer_data.retailers, retailer_group)
    populate_exhibitors(exhibitor_data.exhibitors)
    populate_retailers(retailer_data.retailers)
    populate_shows(show_data.shows)

    return HttpResponseRedirect('/dump/')
