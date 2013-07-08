
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
from django.contrib.admin.views.decorators import staff_member_required

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
from nwkidsshow.forms import AddUserForm

# django query stuff
from django.db.models import Q

# python stuff
import datetime
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

### views ###

def home(request):
    show = Show.objects.filter(end_date__gt=datetime.date.today()).latest('end_date')
    # TODO this still assumes only one active show at a time ever.
    return render_to_response('home.html',
                              {'show': show, },
                              context_instance=RequestContext(request))

def contact(request):
    return render_to_response('contact.html', {}, context_instance=RequestContext(request))

def about(request):
    return render_to_response('about.html', {}, context_instance=RequestContext(request))

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
            # print "### found exhibitor %s" % exhibitor.user
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
            # print "### found retailer %s" % retailer.user
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
    # print "### found exhibitor %s" % exhibitor.user
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
    # Have the exhibitor choose which show to report on.
    # Only let them choose from shows they have registered for.
    exhibitor = Exhibitor.objects.get(user=request.user)
    shows = Show.objects.filter(exhibitors=exhibitor)
    show_count = shows.count()
    show_latest = shows.latest('end_date')
    show_latest_id = show_latest.id
    if request.method != 'POST': # a GET
        form = RetailerReportForm(exhibitor=exhibitor, initial={'show': show_latest_id})
    else: # a POST
        form = RetailerReportForm(request.POST, exhibitor=exhibitor,  initial={'show': show_latest_id})
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
        retailers = Retailer.objects.filter(show=show).exclude(user__first_name='Test').order_by('user__last_name')
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
    show_latest = shows.latest('end_date')
    show_latest_id = show_latest.id
    if request.path == u'/report/exhibitors/':
        title = u'List Exhibitors Registered for a Show'
    else:
        title = u"List Exhibitors' Lines at a Show"
    if request.method != 'POST': # a GET
        form = ExhibitorReportForm(retailer=retailer, initial={'show': show_latest_id})
    else: # a POST
        form = ExhibitorReportForm(request.POST, retailer=retailer,  initial={'show': show_latest_id})
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
        show = Show.objects.get(id=show_id)
        # make sure this retailer has the right to see the exhibitors for this show:
        # that they registered for it
        retailer = Retailer.objects.get(user=request.user)
        registration = RetailerRegistration.objects.get(show=show, retailer=retailer)
        # collect the data for the report: exhibitors at this show
        # TODO: shouldn't I use RetailerRegistrations for this show to get the Retailers?
        exhibitors = Exhibitor.objects.filter(show=show).exclude(user__first_name='Test').order_by('user__last_name')
        # for exhibitor in exhibitors:
        #     pprint(exhibitor)
        rooms = {}
        registrations = Registration.objects.filter(show=show)
        for r in registrations:
            rooms[r.exhibitor.id] = r.room
    except ObjectDoesNotExist:
        return redirect('/advising/noregistration/')
    return render_to_response('report_exhibitors.html',
                              {
                                  'exhibitors': exhibitors,
                                  'show': show,
                                  'rooms': rooms,
                               },
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
    exhibitors = Exhibitor.objects.filter(show=show).exclude(user__first_name='Test')
    lines_dict = {}
    for exhibitor in exhibitors:
        exhibitor_name = '%s %s' % (exhibitor.first_name_display(),exhibitor.last_name_display())
        exhibitor_id = exhibitor.id
        lines_str = exhibitor.lines  # 'aline1 * aline 2 * aline 3'
        # pprint(lines_str)
        lines_list = lines_str.split(' * ')  # ['aline1','aline2','aline3']
        # pprint(lines_list)
        for line in lines_list:
            if line in lines_dict.iterkeys():
                print 'ERROR: line "%s" duplicate detected!' % line
            stripped_line = line.strip()
            if stripped_line:
                lines_dict[stripped_line] = (exhibitor_name, exhibitor_id)
    # pprint(lines_dict)
    # lines_dict.items() makes a list of tuples [('aline','name'),...]
    # case insensitive sort by the line name
    lines_list = sorted(lines_dict.items(), key=lambda t: tuple(t[0].lower()))
    # pprint(lines_list)
    return render_to_response('report_lines.html',
                              {
                                  'show': show,
                                  'lines': lines_list,
                              },
                              context_instance=RequestContext(request))

@login_required(login_url='/advising/login/')
@user_passes_test(user_is_retailer, login_url='/advising/denied/')
def exhibitor(request, exhibitor_id, show_id):
    # make sure this retailer and exhibitor (they want to see) have both registered for this show!
    try:
        show         = Show.objects.get(id=show_id)
        retailer     = Retailer.objects.get(user=request.user)
        RetailerRegistration.objects.get(show=show, retailer=retailer)
        exhibitor    = Exhibitor.objects.get(id=exhibitor_id)
        registration = Registration.objects.get(show=show, exhibitor=exhibitor)
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
    form = None
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
            return redirect('/')
    return render_to_response('add_user.html', {'form': form,}, context_instance=RequestContext(request))

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
        # print "Exhibitor Registration for %s to %s already exists" % (e,s)
    except ObjectDoesNotExist:
        reg = Registration(exhibitor=e, show=s)
        # print "Exhibitor Registration created for %s to %s" % (e,s)
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
            s = Show.objects.get(name=show['name'])
            # print "updating show %s" % s
        except ObjectDoesNotExist:
            s = Show(name=show['name'])
            # print "creating show %s" % s
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

import retailer_data
import exhibitor_data

@staff_member_required
def seed(request):

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
    populate_shows(shows)

    return HttpResponseRedirect('/dump/')
