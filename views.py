
# django request/response stuff
from django.core.context_processors import request
from django.forms.models import model_to_dict
from django.http import HttpResponse
from django.http import Http404
from django.http import HttpResponseRedirect
from django.shortcuts import render_to_response, redirect
from django.template import RequestContext
# django exceptions
from django.core.exceptions import ObjectDoesNotExist

# django authentication
from django.contrib.auth.models import User, Group
from django.contrib.auth.decorators import login_required, user_passes_test
from django.contrib.auth.views import password_change

# my models
from nwkidsshow.models import Exhibitor
from nwkidsshow.models import Retailer
from nwkidsshow.models import Show
from nwkidsshow.models import Registration
from nwkidsshow.models import RetailerRegistration

#my forms
from nwkidsshow.forms import ExhibitorRegistrationForm, RetailerRegistrationForm
from nwkidsshow.forms import ExhibitorForm, RetailerForm
from nwkidsshow.forms import ExhibitorLinesForm
from nwkidsshow.forms import RetailerReportForm
from nwkidsshow.forms import ExhibitorReportForm

# django query stuff
from django.db.models import Q

# python stuff
import datetime
from pprint import pprint

### notes ###
#TODO: I need test accounts that are not real users: "testex" and "testret". Need to hide them from reports, but otherwise work like a real user.
#TODO: why is it looking for this on retailer login? "GET /retailer/home/css/messages.css HTTP/1.1" 404 2991
#TODO: why is it looking for this on exhibitor login?  "GET /exhibitor/home/css/messages.css HTTP/1.1" 404 2994


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

### views ###

def home(request):
    show = Show.objects.filter(end_date__gt=datetime.date.today()).latest('end_date')
    # TODO this still assumes only one active show at a time ever.
    return render_to_response('home.html',
                              {'show': show, },
                              context_instance=RequestContext(request))

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


def get_initial_retailer_registration(retailer, shows):
    try:
        registration = RetailerRegistration.objects.get(show=shows[0], retailer=retailer)
    except ObjectDoesNotExist:
        return {}
    # pprint(model_to_dict(registration))
    return model_to_dict(registration)

def get_initial_exhibitor_registration(exhibitor, shows):
    try:
        registration = Registration.objects.get(show=shows[0], exhibitor=exhibitor)
    except ObjectDoesNotExist:
        return {}
    # pprint(model_to_dict(registration))
    return model_to_dict(registration)

@login_required(login_url='/advising/login/')
@user_passes_test(user_is_exhibitor_or_retailer, login_url='/advising/denied/')
def register(request):
    shows = Show.objects.filter(closed_date__gt=datetime.date.today())
    show_count = shows.count()
    form = None

    if request.method != 'POST': # a GET

        if user_is_retailer(request.user):
            retailer = Retailer.objects.get(user=request.user)
            form = RetailerRegistrationForm(
                initial=get_initial_retailer_registration(retailer, shows),
                better_choices=get_better_choices(shows, show_count)
            )

        if user_is_exhibitor(request.user):
            exhibitor = Exhibitor.objects.get(user=request.user)
            form = ExhibitorRegistrationForm(
                initial=get_initial_exhibitor_registration(exhibitor, shows)
            )

    else: # a POST

        if user_is_exhibitor(request.user):
            #TODO: do I need to test this found one thing? try/catch.
            exhibitor = Exhibitor.objects.get(user=request.user)
            print "### found exhibitor %s" % exhibitor.user
            form = ExhibitorRegistrationForm(request.POST)
            if form.is_valid():
                cd = form.cleaned_data

                # grab some fields form the form
                show           = cd['show']
                num_associates = cd['num_associates']
                num_assistants = cd['num_assistants']
                num_racks      = cd['num_racks']
                num_tables     = cd['num_tables']
                is_late        = cd['show'].late_date < datetime.date.today()

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
                r.date_registered    = datetime.date.today()
                r.registration_total = registration_total
                r.assistant_total    = assistant_total
                r.rack_total         = rack_total
                r.late_total         = late_total
                r.total              = total
                r.save()

                # display the show info, fees, disclaimers, etc. on a nice page
                return redirect('/invoice/%s/' % show.id)
        else:
            #TODO: do I need to test this found one thing? try/catch.
            retailer = Retailer.objects.get(user=request.user)
            print "### found retailer %s" % retailer.user
            form = RetailerRegistrationForm(request.POST, better_choices=get_better_choices(shows, show_count))
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
@user_passes_test(user_is_retailer, login_url='/advising/denied/')
def registrations(request):
    retailer = Retailer.objects.get(user=request.user)
    regs = RetailerRegistration.objects.filter(retailer=retailer)
    return render_to_response('registrations.html', {'registrations': regs},
                              context_instance=RequestContext(request))

@login_required(login_url='/advising/login/')
@user_passes_test(user_is_retailer, login_url='/advising/denied/')
def registered(request, show_id):
    try:
        show = Show.objects.get(id=show_id)
        retailer = Retailer.objects.get(user=request.user)
        registration = RetailerRegistration.objects.get(show=show, retailer=retailer)
    except ObjectDoesNotExist:
        return redirect('/advising/noregistration/')
    return render_to_response('registered.html', {'show': show, 'registration': registration},
                              context_instance=RequestContext(request))

@login_required(login_url='/advising/login/')
@user_passes_test(user_is_exhibitor, login_url='/advising/denied/')
def invoices(request):
    exhibitor = Exhibitor.objects.get(user=request.user)
    print "### found exhibitor %s" % exhibitor.user
    invoices = Registration.objects.filter(exhibitor=exhibitor)
    return render_to_response('invoices.html', {'invoices': invoices},
                              context_instance=RequestContext(request))

@login_required(login_url='/advising/login/')
@user_passes_test(user_is_exhibitor, login_url='/advising/denied/')
def invoice(request, showid):
    try:
        show = Show.objects.get(id=showid)
        exhibitor = Exhibitor.objects.get(user=request.user)
        registration = Registration.objects.get(show=show, exhibitor=exhibitor)
    except ObjectDoesNotExist:
        return redirect('/advising/noinvoice/')
    return render_to_response('invoice.html', {'show': show, 'registration': registration},
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
    lines_dict = {} # {'line_0':'aline1', 'line_1':'aline2', 'line_2':'aline3' }
    for i in xrange(num_lines):
        lines_dict['line_%i' % i] = lines_list[i]
    # pprint(lines_dict)
    if request.method != 'POST': # a GET
        form = ExhibitorLinesForm(num_lines=num_lines, initial=lines_dict)
    else:
        form = ExhibitorLinesForm(request.POST, num_lines=num_lines)
        if form.is_valid():
            lines_dict = form.cleaned_data # {'line_0': u'aline1', 'line_1': u'aline2', 'line_2': u'aline3'}
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
    # Have the exhibitor choose which show to report on.
    # Only let them choose from shows they have registered for.
    exhibitor = Exhibitor.objects.get(user=request.user)
    shows = Show.objects.filter(exhibitors=exhibitor)
    show_count = shows.count()
    if request.method != 'POST': # a GET
        form = RetailerReportForm(exhibitor=exhibitor)
    else: # a POST
        form = RetailerReportForm(request.POST, exhibitor=exhibitor)
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
        show = Show.objects.get(id=show_id)
        # make sure this exhibitor has the right to see the retailers for this show:
        # that they registered for it
        exhibitor = Exhibitor.objects.get(user=request.user)
        registration = Registration.objects.get(show=show, exhibitor=exhibitor)
        # collect the data for the report: retailers at this show
        # TODO: shouldn't I use RetailerRegistrations for this show to get the Retailers?
        retailers = Retailer.objects.filter(show=show).order_by('user__last_name')
        # for retailer in retailers:
        #     pprint(retailer)
    except ObjectDoesNotExist:
        return redirect('/advising/noregistration/')
    return render_to_response('report_retailers.html', {'retailers': retailers, 'show': show},
                              context_instance=RequestContext(request))

@login_required(login_url='/advising/login/')
@user_passes_test(user_is_retailer, login_url='/advising/denied/')
def report_exhibitors_form(request):
    # Have the retailer choose which show to report on.
    # Only let them choose from shows they have registered for.
    retailer = Retailer.objects.get(user=request.user)
    shows = Show.objects.filter(retailers=retailer)
    show_count = shows.count()
    if request.path == u'/report/exhibitors/':
        title = u'List Exhibitors at a Show'
    else:
        title = u"List Exhibitors' Lines at a Show"
    if request.method != 'POST': # a GET
        form = ExhibitorReportForm(retailer=retailer)
    else: # a POST
        form = ExhibitorReportForm(request.POST, retailer=retailer)
        if form.is_valid():
            cd = form.cleaned_data
            show = cd['show']
            pprint(request.path)
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
        show = Show.objects.get(id=show_id)
        # make sure this retailer has the right to see the exhibitors for this show:
        # that they registered for it
        retailer = Retailer.objects.get(user=request.user)
        registration = RetailerRegistration.objects.get(show=show, retailer=retailer)
        # collect the data for the report: exhibitors at this show
        # TODO: shouldn't I use RetailerRegistrations for this show to get the Retailers?
        exhibitors = Exhibitor.objects.filter(show=show).order_by('user__last_name')
        # for exhibitor in exhibitors:
        #     pprint(exhibitor)
    except ObjectDoesNotExist:
        return redirect('/advising/noregistration/')
    return render_to_response('report_exhibitors.html', {'exhibitors': exhibitors, 'show': show},
                              context_instance=RequestContext(request))


@login_required(login_url='/advising/login/')
@user_passes_test(user_is_retailer, login_url='/advising/denied/')
def report_lines(request, show_id):
    try:
        show = Show.objects.get(id=show_id)
        # make sure this retailer has the right to see the exhibitors for this show:
        # that they registered for it
        retailer = Retailer.objects.get(user=request.user)
        registration = RetailerRegistration.objects.get(show=show, retailer=retailer)
    except ObjectDoesNotExist:
        return redirect('/advising/noregistration/')
    # collect the data for the report: all the lines at the show with exhibitor name (first,last)
    # TODO: shouldn't I use RetailerRegistrations for this show to get the Retailers?
    exhibitors = Exhibitor.objects.filter(show=show)
    lines_dict = {}
    for exhibitor in exhibitors:
        lines_str = exhibitor.lines # 'aline1 * aline 2 * aline 3'
        # pprint(lines_str)
        lines_list = lines_str.split(' * ') # ['aline1','aline2','aline3']
        # pprint(lines_list)
        for line in lines_list:
            if line in lines_dict.iterkeys():
                print 'ERROR: line "%s" duplicate detected!' % line
            lines_dict[line] = '%s %s' % (exhibitor.first_name_display(),exhibitor.last_name_display())
    # pprint(lines_dict)
    # lines_dict.items() makes a list of tuples [('aline','name'),...]
    # case insensitive sort by the line name
    lines_list = sorted(lines_dict.items(), key=lambda t: tuple(t[0].lower()))
    # pprint(lines_list_of_tuples_sorted)
    return render_to_response('report_lines.html', {'show': show, 'lines': lines_list},
                              context_instance=RequestContext(request))


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
            print "user already exists: %s (%s)" % (u.username, u.get_full_name())
        except ObjectDoesNotExist:
            u = User.objects.create_user(username=user['username'])
            print "created user: %s" % u.username
        u.first_name = user['first_name'] if not u.first_name else u.first_name
        u.last_name  = user['last_name']  if not u.last_name else u.last_name
        u.email      = user['email']      if not u.email else u.email
        if not u.password or not u.has_usable_password():
            u.set_password(user['password'])
            print 'set %s password to %s' % (u.get_full_name(), user['password'])
        else:
            print 'password for %s is %s' % (u.get_full_name(), u.password)
        u.save()
        u.groups.add(group)
    return

# hey, this looks a lot like Exhibitor.objects.all().values()
#    {
#        'username': '',
#        'password': 'password',
#        'first_name': '',
#        'last_name': '',
#        'email': '',
#        'company': '',
#        'website': '',
#        'address': '',
#        'address2': '',
#        'city': '',
#        'state': '',
#        'zip': '',
#        'phone': '',
#        'fax': '',
#        'lines': """ """,
#    },
exhibitors = [
    {
        'username': 'testex',
        'password': 'testex',
        'first_name': 'Test',
        'last_name': 'Exhibitor',
        'email': 'info@nwkidsshow.com',
        'company': 'Laurel Event Management',
        'website': 'http://www.nwkidsshow.com/',
        'address': '17565 SW 108th place',
        'address2': '',
        'city': 'Tualatin',
        'state': 'OR',
        'zip': '97062',
        'phone': '503-330-7167',
        'fax': '503-555-1212',
        'lines': """no * lines * really""",
    },
    {
        'username': 'allison_acken',
        'password': 'password',
        'first_name': 'Allison',
        'last_name': 'Acken',
        'email': 'allisonshowroom@gmail.com',
        'company': '',
        'website': '',
        'address': '',
        'address2': '',
        'city': 'Los Angeles',
        'state': 'CA',
        'zip': '',
        'phone': '310-486-9354',
        'fax': '',
        'lines': """Kanz * Wheat * Purebaby Organic * Finn and Emma Organic""",
    },
    {
        'username': 'randee_arneson',
        'password': 'password',
        'first_name': 'Randee',
        'last_name': 'Arneson',
        'email': 'randeesshowroom@gmail.com',
        'company': '',
        'website': '',
        'address': '',
        'address2': '',
        'city': '',
        'state': '',
        'zip': '',
        'phone': '213-624-8422',
        'fax': '213-624-8946',
        'lines': """Petit Lem * Me Too * Losan * Blueberry Hill * Melton * Monkeybar Buddies * Nosilla Organics * She's the One * Thingamajiggies, PJ's * Marmalade * Ollie Baby * Nadi A Biffi * Imagine Greenwear * Rose Cage * Everbloom Studio * Polka Dot Moon * Milla Reese Hair accessories * Toni Tierney""",
    },
    {
        'username': 'nancy_camus',
        'password': 'password',
        'first_name': 'Nancy',
        'last_name': 'Camus',
        'email': 'info@paperdollstyleshowroom.com',
        'company': '',
        'website': '',
        'address': '',
        'address2': '',
        'city': 'Los Angeles',
        'state': 'CA',
        'zip': '',
        'phone': '213-629-9874',
        'fax': '213-629-9875',
        'lines': """Chibella * Livie & Luca * Feather Baby * The Happy Closet * Decaf Plush * Just Fab Girls * Smile Squared""",
    },
    {
       'username': 'jack_chapman',
       'password': 'password',
       'first_name': 'Jack',
       'last_name': 'Chapman',
       'email': 'jackc@net-venture.com',
       'company': '',
       'website': '',
       'address': '',
       'address2': '',
       'city': 'University Place',
       'state': 'WA',
       'zip': '',
       'phone': '253-235-1870',
       'fax': '',
       'lines': """Just Be * Worry Woos * Our Globo * Robot Luv * Stikiis""",
   },
    {
       'username': 'helene_cohen',
       'password': 'password',
       'first_name': 'Helene',
       'last_name': 'Cohen',
       'email': 'toohotusa@aol.com',
       'company': '',
       'website': '',
       'address': '',
       'address2': '',
       'city': 'Los Angeles',
       'state': 'CA',
       'zip': '',
       'phone': '213-627-5773',
       'fax': '213-629-2479',
       'lines': """Lazy One Sleep Wear * Sozo * Agabang * Happy Mermaid Dresses * Boker & Laila Pajamas * Zopheez * 2 Red Hens * Mini zzz * Sovereign * Tortle Hats""",
   },
    {
       'username': 'nicky_coscas',
       'password': 'password',
       'first_name': 'Nicky',
       'last_name': 'Coscas',
       'email': 'nicky@nickyrosekids.com',
       'company': '',
       'website': '',
       'address': '',
       'address2': '',
       'city': '',
       'state': '',
       'zip': '',
       'phone': '213-593-1322   ',
       'fax': '213-593-1323',
       'lines': """7 For All Mankind Kids * City Threads * Egg by Susan Lazar * Juicy Couture Baby * Kiniki * LA Made kids * Ode * PAIGELAUREN baby * The Green Egg""",
   },
    {
       'username': 'susie_cinningham',
       'password': 'password',
       'first_name': 'Susie',
       'last_name': 'Cunningham',
       'email': 'susiesunkid@yahoo.com',
       'company': '',
       'website': '',
       'address': '',
       'address2': '',
       'city': 'Portland',
       'state': 'OR',
       'zip': '',
       'phone': '503-230-1219',
       'fax': '503-231-3554',
       'lines': """Roxy Girl * Roxy Teenie Wahine * Quiksilver Boys & Baby * Country Kids Legwear * No Slippy Hair Clippy""",
   },
    {
       'username': 'gloria_davis',
       'password': 'password',
       'first_name': 'Gloria',
       'last_name': 'Davis',
       'email': 'gloriapdavis@sbcglobal.net',
       'company': '',
       'website': '',
       'address': '',
       'address2': '',
       'city': 'San Francisco',
       'state': 'CA',
       'zip': '',
       'phone': '415-297-3906',
       'fax': '888-511-6990',
       'lines': """SnoPea, Inc. * Preemie Yums * Mack & Co. * Two Flowers One Bear * Bear Hands & Buddies * Million Polkadots""",
   },
    {
       'username': 'linsey_ebuen',
       'password': 'password',
       'first_name': 'Linsey',
       'last_name': 'Ebuen',
       'email': 'linsey.ebuen@guavakids.com',
       'company': '',
       'website': '',
       'address': '',
       'address2': '',
       'city': 'Beaverton',
       'state': 'OR',
       'zip': '',
       'phone': '503-327-4868',
       'fax': '888-946-4828',
       'lines': """GuavaKids""", #TODO: test this! one entry, no delimiters.
   },
    {
       'username': 'joann_farese',
       'password': 'password',
       'first_name': 'JoAnn',
       'last_name': 'Farese',
       'email': 'j_farese@sbcglobal.net',
       'company': '',
       'website': '',
       'address': '',
       'address2': '',
       'city': 'San Francisco',
       'state': 'CA',
       'zip': '',
       'phone': '415-742-5422',
       'fax': '415-661-2296',
       'lines': """Crocs Kids Apparel * Crocs Accessories * Colette Kids * Girl & Co. * Lime Apple * New Jammies * Origany * Real Kids Shades * Wayi Bamboo * Wugbug * Breganwood Organics * Shinobi Baby""",
   },
    {
       'username': 'afton_farley',
       'password': 'password',
       'first_name': 'Afton',
       'last_name': 'Farley',
       'email': 'afton@redwagonbaby.com',
       'company': '',
       'website': '',
       'address': '',
       'address2': '',
       'city': 'Los Angeles',
       'state': 'CA',
       'zip': '',
       'phone': '310-569-0366',
       'fax': '',
       'lines': """Red Wagon Baby * June Kids""",
   },
    {
       'username': 'sylvia_gill',
       'password': 'password',
       'first_name': 'Sylvia',
       'last_name': 'Gill',
       'email': 'showroom@sylviagill.com',
       'company': '',
       'website': '',
       'address': '',
       'address2': '',
       'city': 'San Francisco',
       'state': 'CA',
       'zip': '',
       'phone': '415-255-9899',
       'fax': '415-255-9929',
       'lines': """Kissy Kissy * Newborn by Mayoral * Mulberribush * Love U Lots * Down East Girls * Haven Girl * Little Handprint * Lollipop Twirl * Flap Happy * Zoocchini * Bows Arts * Konfetti * Kai Kreations * Ragtop - Neptune Zoo""",
   },
    {
       'username': 'sandra_gorecke',
       'password': 'password',
       'first_name': 'Sandra',
       'last_name': 'Gorecke',
       'email': 'showroomalamode@gmail.com',
       'company': '',
       'website': '',
       'address': '',
       'address2': '',
       'city': 'Los Angeles',
       'state': 'CA',
       'zip': '',
       'phone': '213-393-7097',
       'fax': '213-995-9862',
       'lines': """I DO * Mini banda * Sarrabanda * Silvian Heach * Imoga * Bari Lynn hair accessories * Tutim NYC""",
   },
    {
       'username': 'angela_hansen',
       'password': 'password',
       'first_name': 'Angela',
       'last_name': 'Grosvenor Hansen',
       'email': 'evergreenrep@frontier.com',
       'company': '',
       'website': '',
       'address': '',
       'address2': '',
       'city': 'Duvall',
       'state': 'WA',
       'zip': '',
       'phone': '425-844-1431',
       'fax': '425-844-1431',
       'lines': """Babalu * Baby Buddha Studio * Bunnies by the Bay * Creative Education * Do A Dot * Eco Kids * Elope * Endangered Species * European Expressions * Fish River Crafts * GeoToys * Groovy Holidays * Independent Pub Group * Just Jump It * KaZAM Bikes * Kid's Preferred * Kiss Naturals * Klein * Klean Kanteen * Legendary Games * Light-Beams * Magic Forest * Maxim Enterprises * Meadowview Imports * Mindtwister USA * minina * Moonjar * Pacific Play Tent * Piggy Paint * ReUsies * Sentosphere * TWC of America * Ulubulu * Uncle Goose * Warm Fuzzy * WoolPets""",
   },
    {
       'username': 'betsy_harney',
       'password': 'password',
       'first_name': 'Betsy',
       'last_name': 'Harney',
       'email': 'contact@sugarbsales.com',
       'company': '',
       'website': '',
       'address': '',
       'address2': '',
       'city': 'Renton',
       'state': 'WA',
       'zip': '',
       'phone': '425-277-5499',
       'fax': '800-783-9875',
       'lines': """Dabbawalla Bags * Douglas Company * eeBoo * Jack Rabbit * Kid Style * Lunch Bots * Merry Makers * P'Kolino * Rich Frog * Tullie Girl""",
   },
    {
       'username': 'tanya_hawkins',
       'password': 'password',
       'first_name': 'Tanya',
       'last_name': 'Hawkins',
       'email': 'monkeybizreps@gmail.com',
       'company': '',
       'website': '',
       'address': '',
       'address2': '',
       'city': 'Portland',
       'state': 'OR',
       'zip': '',
       'phone': '503-799-6221',
       'fax': '503-244-9914',
       'lines': """Petunia Pickle Bottom * See Kai Run * Trumpette * Bebe au lait * Magnificent Baby * Minnie & Lola * Zootie B Little * Giddy Giddy * Noodle & Boo * Crawlings * Tadpole & Lily * Via Cacao""",
   },
    {
       'username': 'cristy_howe',
       'password': 'password',
       'first_name': 'Cristy',
       'last_name': 'Howe',
       'email': 'cristy@teacollection.com',
       'company': '',
       'website': '',
       'address': '',
       'address2': '',
       'city': 'Los Angeles',
       'state': 'CA',
       'zip': '',
       'phone': '805-746-4985',
       'fax': '415-321-2478',
       'lines': """Tea Collection""", # TODO test this with one entry
   },
    {
       'username': 'judy_johnson',
       'password': 'password',
       'first_name': 'Judy',
       'last_name': 'Johnson',
       'email': 'jj.sales@comcast.net',
       'company': '',
       'website': '',
       'address': '',
       'address2': '',
       'city': 'Portland',
       'state': 'OR',
       'zip': '',
       'phone': '503-246-5707',
       'fax': '503-452-8840',
       'lines': """ """,
   },
    {
       'username': 'sarah_kaufman',
       'password': 'password',
       'first_name': 'Sarah',
       'last_name': 'Kaufman',
       'email': 'sarahco@att.net',
       'company': '',
       'website': '',
       'address': '',
       'address2': '',
       'city': 'San Francisco',
       'state': 'CA',
       'zip': '',
       'phone': '415-379-4400',
       'fax': '415-379-4341',
       'lines': """Le Top * Le Top Baby * Rabbitmoon* Hartstrings * KC Parker * Wee Ones * Pluie Pluie Rainwear * Foxfire Rainwear * Tuff Kookooshka * Apollo sock & tights * David Fussenegger blankets * L'Amour shoes * Knot Genie""",
   },
    {
       'username': 'july_krause',
       'password': 'password',
       'first_name': 'July',
       'last_name': 'Krause',
       'email': 'wendyscloset@gmail.com',
       'company': '',
       'website': '',
       'address': '',
       'address2': '',
       'city': 'Los Angeles',
       'state': 'CA',
       'zip': '',
       'phone': '213-627-9506',
       'fax': '213-627-8695',
       'lines': """Winter Water Factory * Nano * Lily and Momo * Sweet Peanut * Ooh La La Couture * Luna Leggings * Persnickety Clothing * Silkberry Baby * IDA - T Denmark * Shampoodle * Joyfolie Shoes * Liv & Lily * Chewbeads * Old Soles Shoes * NOHI Organics""",
   },
    {
       'username': 'betty_lewis',
       'password': 'password',
       'first_name': 'Betty',
       'last_name': 'Lewis',
       'email': 'betty@bettylewissales.com',
       'company': '',
       'website': '',
       'address': '',
       'address2': '',
       'city': 'Lakebay',
       'state': 'WA',
       'zip': '',
       'phone': '888-732-6103',
       'fax': '866-902-1401',
       'lines': """i Play/green sprouts * Kushies Basics * Halo Innovations * Sock Ons * Baby Jogger * Recaro Car Seats * Moonlight Slumber * 4moms""",
   },
    {
       'username': 'sandra_martinez',
       'password': 'password',
       'first_name': 'Sandran',
       'last_name': 'Martinez',
       'email': 'info@inplayshowroom.com',
       'company': '',
       'website': '',
       'address': '',
       'address2': '',
       'city': 'Los Angeles',
       'state': 'CA',
       'zip': '',
       'phone': '213-489-7908',
       'fax': '',
       'lines': """Appaman * Chaser Kids * Diaper Dude * Me In Mind * Native Shoes * Mini Maniacs Bibs * Modern Lux (Tween) * Prefresh""",
   },
    {
       'username': 'leslie_nielsen',
       'password': 'password',
       'first_name': 'Leslie',
       'last_name': 'Nielsen',
       'email': 'lesniel@comcast.net',
       'company': '',
       'website': '',
       'address': '',
       'address2': '',
       'city': 'Seattle',
       'state': 'WA',
       'zip': '',
       'phone': '206-937-6013',
       'fax': '206-937-1778',
       'lines': """Mimi & Maggie * Angel Dear * Little Sea Gems * Chooze Shoes * Huggalugs""",
   },
    {
       'username': 'bob_parrish',
       'password': 'password',
       'first_name': 'Bob',
       'last_name': 'Parrish',
       'email': 'bobparrish@sbcglobal.net',
       'company': '',
       'website': '',
       'address': '',
       'address2': '',
       'city': 'Martinez',
       'state': 'CA',
       'zip': '',
       'phone': '925-228-5696',
       'fax': '925-228-5699',
       'lines': """Isobella & Chloe * Dogwood * Betty Ann Hats * Milsky Belts * Elegantbaby * Peaceable Kingdom * Purple Mountains Ice Caps & Hats * Pickles Footwear * Squeak-Me-Shoes * Plum/Plum Pudding * Pink Ginger * Up and Away Jackets * Bonne * La Piccola Danza""",
   },
    {
       'username': 'colleen_post',
       'password': 'password',
       'first_name': 'Colleen',
       'last_name': 'Post',
       'email': 'postc@comcast.net',
       'company': '',
       'website': '',
       'address': '',
       'address2': '',
       'city': 'Tigard',
       'state': 'OR',
       'zip': '',
       'phone': '503-579-2409',
       'fax': '503-590-8198',
       'lines': """Under the Nile * Beba Bean * Wry Baby * Funkie Baby * Kiwi""",
   },
    {
       'username': 'robert_prescott',
       'password': 'password',
       'first_name': 'Robert',
       'last_name': 'Prescott',
       'email': 'rd@youngcolors.com',
       'company': '',
       'website': '',
       'address': '',
       'address2': '',
       'city': 'Salida',
       'state': 'CO',
       'zip': '',
       'phone': '719-539-3812',
       'fax': '719-539-3813',
       'lines': """Young Colors * Frumpy Rumps *Silly Sarongs * Young Colors Hats * College Colors""",
   },
    {
       'username': 'julie_smith',
       'password': 'password',
       'first_name': 'Julie',
       'last_name': 'Smith',
       'email': 'julie@juliesmithkids.com',
       'company': '',
       'website': '',
       'address': '',
       'address2': '',
       'city': 'Los Angeles',
       'state': 'CA',
       'zip': '',
       'phone': '213-622-4643',
       'fax': '213-622-7451',
       'lines': """Mayoral * Urban Sunday * Yosi Samra Shoes * Ciao Marco * Zutano * Timi and Leslie * Little Joules * M. Andonia * Sossabella Jewelry * Laundry by Shelli Segal""",
   },
    {
       'username': 'teresa_stephen',
       'password': 'password',
       'first_name': 'Teresa',
       'last_name': 'Stephen',
       'email': 'krystal@teresasroom.com',
       'company': '',
       'website': '',
       'address': '',
       'address2': '',
       'city': 'Los Angeles',
       'state': 'CA',
       'zip': '',
       'phone': '866-723-5437',
       'fax': '213-612-0227',
       'lines': """Little Me * Offspring * Nannette * Popatu by Posh Int'l. * Peaches'n Cream * Mallory May * Mollie & Millie * Guess Kids * Flapdoodles * Wee Squeak Shoes * Tommy Tickle * Bobux * AM PM Kids * Fancy That Hat * Hide-ees * Kensie Girl * Fun Apparel""",
   },
    {
       'username': 'joanne_torres',
       'password': 'password',
       'first_name': 'Joanne',
       'last_name': 'Torres',
       'email': 'showroom@lolajosales.com',
       'company': '',
       'website': '',
       'address': '',
       'address2': '',
       'city': 'Los Angeles',
       'state': 'CA',
       'zip': '',
       'phone': '213-623-0993',
       'fax': '213-244-9645',
       'lines': """New ICM/Laura Dare * Little Adventures * Max Daniel Blankets * Luli and Me * Hello Kitty * Baby Bling * Sara Kety * Julius Berger * Malibu Swimwear * Ska Doo Shoes * Carriage Boutique * Boutique Collection * Feltman * Toe Blooms * Woolrich * Drench Raingear * Baby Buns""",
   },
    {
       'username': 'cathe_verdusco',
       'password': 'password',
       'first_name': 'Cathe',
       'last_name': 'Verdusco',
       'email': 'jody@smallshopshowroom.com',
       'company': '',
       'website': '',
       'address': '',
       'address2': '',
       'city': 'Los Angeles',
       'state': 'CA',
       'zip': '',
       'phone': '213-488-0090',
       'fax': '213-488-0040',
       'lines': """Charlie Rocket * Desigual * Maisonette * Mini & Maximus * Shwings * Milk & Soda * Curio & Kind * La Piccola Danza * Big Citizen * SuperTrash""",
   },
    {
       'username': 'don_welborn',
       'password': 'password',
       'first_name': 'Don',
       'last_name': 'Welborn',
       'email': 'sales@donwelborn.com',
       'company': '',
       'website': '',
       'address': '',
       'address2': '',
       'city': 'Los Angeles',
       'state': 'CA',
       'zip': '',
       'phone': '213-688-4953',
       'fax': '213-688-0165',
       'lines': """Vitamins Baby * Absorba * Kushies * Zaza Couture * Donita * Intakt * Kids Republic Dx Xtreme * Trimfit * Globaltex Kids * Ben Sherman * French Connection * Firetrap""",
   },
]


def populate_exhibitors(exhibitors):
    for exhibitor in exhibitors:
        user = User.objects.get(username=exhibitor['username']) # had better be one already!
        try:
            e = Exhibitor.objects.get(user=user)
            print "updating exhibitor %s" % e
        except ObjectDoesNotExist:
            e = Exhibitor(user=user)
            print "creating exhibitor %s" % e
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
        e.must_change_password = False
        e.save()
    return


#    {
#        'username': '',
#        'password': 'password',
#        'first_name': '',
#        'last_name': '',
#        'email': '',
#        'company': '',
#        'website': '',
#        'address': '',
#        'address2': '',
#        'city': '',
#        'state': '',
#        'zip': '',
#        'phone': '',
#        'fax': '',
#        },
retailers = [
    {
        'username': 'testre',
        'password': 'testre',
        'first_name': 'Tester',
        'last_name': 'Tester',
        'email': 'info@nwkidsshow.com',
        'company': 'Laurel Event Management',
        'website': 'http://www.nwkidsshow.com/',
        'address': '17565 SW 108th Place',
        'address2': '',
        'city': 'Tualatin',
        'state': 'OR',
        'zip': '97062',
        'phone': '503-330-7167',
        'fax': '503-555-1212',
        },
    {
        'username': 'jessica_thompson',
        'password': 'password',
        'first_name': 'Jessica',
        'last_name': 'Thompson',
        'email': 'jesthompson2010@gmail.com',
        'company': '',
        'website': '',
        'address': '',
        'address2': '',
        'city': '',
        'state': '',
        'zip': '',
        'phone': '253-858-1147',
        'fax': '',
    },
    {
        'username': 'reese_prouty',
        'password': 'password',
        'first_name': 'Reese',
        'last_name': 'Prouty',
        'email': '',
        'company': '8 Women',
        'website': '', 'address': '3614 SE Hawthorne',
        'address2': '',
        'city': 'Portland',
        'state': 'OR',
        'zip': '97214',
        'phone': '503-236-8878',
        'fax': '',
    },
]

def populate_retailers(retailers):
    for retailer in retailers:
        user = User.objects.get(username=retailer['username']) # had better be one already!
        try:
            r = Retailer.objects.get(user=user)
            print "updating retailer %s" % r
        except ObjectDoesNotExist:
            r = Retailer(user=user)
            print "creating retailer %s" % r
        r.company   = retailer['company']  if not r.company  else r.company
        r.website   = retailer['website']  if not r.website  else r.website
        r.address   = retailer['address']  if not r.address  else r.address
        r.address2  = retailer['address2'] if not r.address2 else r.address2
        r.city      = retailer['city']     if not r.city     else r.city
        r.state     = retailer['state']    if not r.state    else r.state
        r.phone     = retailer['phone']    if not r.phone    else r.phone
        r.zip       = retailer['zip']      if not r.zip      else r.zip
        r.fax       = retailer['fax']      if not r.fax      else r.fax
        r.must_change_password = False
        r.save()
    return

shows = [
    {
        'name'       : 'February 2013',
        'late_date'  : datetime.date(2012, 12, 24),
        'closed_date': datetime.date(2013,  1, 24),
        'start_date' : datetime.date(2013,  2, 24),
        'end_date'   : datetime.date(2013,  2, 26),
        'registration_fee' : 150.00,
        'assistant_fee'    : 25.00,
        'late_fee'         : 75.00,
        'rack_fee'         : 20.00,
    },
    {
        'name'       : 'September 2013',
        'late_date'  : datetime.date(2013,  7, 26),
        'closed_date': datetime.date(2013,  8,  9),
        'start_date' : datetime.date(2013,  9, 28),
        'end_date'   : datetime.date(2013,  9, 30),
        'registration_fee' : 150.00,
        'assistant_fee'    : 25.00,
        'late_fee'         : 75.00,
        'rack_fee'         : 20.00,
    },
    # {
    #     'name'       : 'February 2014',
    #     'late_date'  : datetime.date(2013, 12, 24),
    #     'closed_date': datetime.date(2014,  1, 24),
    #     'start_date' : datetime.date(2014,  2, 22),
    #     'end_date'   : datetime.date(2014,  2, 24),
    #     'registration_fee' : 150.00,
    #     'assistant_fee'    : 25.00,
    #     'late_fee'         : 75.00,
    #     'rack_fee'         : 20.00,
    # },
]


def register_exhibitor(e,s):
    try:
        reg = Registration.objects.get(exhibitor=e, show=s)
        print "Exhibitor Registration for %s to %s already exists" % (e,s)
    except ObjectDoesNotExist:
        reg = Registration(exhibitor=e, show=s)
        print "Exhibitor Registration created for %s to %s" % (e,s)
        reg.num_exhibitors = 0
        reg.num_assistants = 0
        reg.num_racks = 0
        reg.num_tables = 0
        reg.is_late = False
        reg.date_registered = datetime.date.today()
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
        print "Retailer Registration for %s to %s already exists" % (r,s)
    except ObjectDoesNotExist:
        reg = RetailerRegistration(retailer=r, show=s)
        print "Retailer Registration created for %s to %s" % (r,s)
        reg.num_attendees = 0
        reg.days_attending = "0"
        reg.save()


def populate_shows(shows):
    #Show.objects.all().delete()
    for show in shows:
        try:
            s = Show.objects.get(name=show['name'])
            print "updating show %s" % s
        except ObjectDoesNotExist:
            s = Show(name=show['name'])
            print "creating show %s" % s
        s.late_date   = show['late_date']   if not s.late_date   else s.late_date
        s.closed_date = show['closed_date'] if not s.closed_date else s.closed_date
        s. start_date = show['start_date']  if not s.start_date  else s.start_date
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

def seed(request):

    exhibitor_group, created = Group.objects.get_or_create(name='exhibitor_group')
    if created:
        print "created new exhibitor_group"
    else:
        print "exhibitor_group already exists"
    retailer_group,  created = Group.objects.get_or_create(name='retailer_group')
    if created:
        print "created new retailer_group"
    else:
        print "retailer_group already exists"

    populate_users(exhibitors, exhibitor_group)
    populate_users(retailers, retailer_group)
    populate_exhibitors(exhibitors)
    populate_retailers(retailers)
    populate_shows(shows)

    return HttpResponseRedirect('/dump/')
