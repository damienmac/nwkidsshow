
# django request/response stuff
from django.http import HttpResponse
from django.http import Http404
from django.http import HttpResponseRedirect
from django.shortcuts import render_to_response, redirect

# django exceptions
from django.core.exceptions import ObjectDoesNotExist

# django authentication
from django.contrib.auth.models import User, Group
from django.contrib.auth.decorators import login_required, user_passes_test

# my models
from nwkidsshow.models import Exhibitor
from nwkidsshow.models import Retailer
from nwkidsshow.models import Show

# python stuff
import datetime

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

### views ###

def home(request):
    return render_to_response('home.html', {'world_kind':'happy'})

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
    # TODO log an error, this shold not happen, they logged in after all!
    return redirect('/')
    

@login_required
@user_passes_test(user_is_exhibitor, login_url='/advising/denied/')
def exhibitor_home(request):
    return render_to_response('home.html', {'world_kind':'exhibitor home'})

@login_required
@user_passes_test(user_is_retailer, login_url='/advising/denied/')
def retailer_home(request):
    return render_to_response('home.html', {'world_kind':'retailer home'})

def dump(request):
    users      = User.objects.all()
    exhibitors = Exhibitor.objects.all()
    retailers  = Retailer.objects.all()
    shows      = Show.objects.all()
    return render_to_response('dump.html', { 
                                            'users'      : users,
                                            'exhibitors' : exhibitors,
                                            'retailers'  : retailers,
                                            'shows'      : shows,
                                            })

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
#        {'username':'', 'password':'', 'first_name':'', 'last_name':'', 'email':'', 'company':'', 'address':'', 'address2':'', 'city':'', 'state':'', 'phone':'', 'fax':'', lines':""" """, },
exhibitors = [
         {'username':'allison', 'password':'password', 'first_name':'Allison', 'last_name':'Acken',   'email':'allisonshowroom@gmail.com', 'company':'', 'website':'', 'address':'', 'address2':'', 'city':'Los Angeles', 'state':'CA', 'zip':'', 'phone':'310-486-9354', 'fax':'', 'lines':"""Kanz * Wheat * Purebaby Organic * Finn and Emma Organic""", },
         {'username':'randee',  'password':'password', 'first_name':'Randee',  'last_name':'Arneson', 'email':'randeesshowroom@gmail.com', 'company':'', 'website':'', 'address':'', 'address2':'', 'city':'', 'state':'', 'zip':'', 'phone':'213-624-8422', 'fax':'213-624-8946', 'lines':"""Petit Lem * Me Too * Losan * Blueberry Hill * Melton * Monkeybar Buddies * Nosilla Organics * She's the One * Thingamajiggies, PJ's * Marmalade * Ollie Baby * Nadi A Biffi * Imagine Greenwear *  Rose Cage * Everbloom Studio * Polka Dot Moon * Milla Reese Hair accessories * Toni Tierney""", },
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
        e.address   = exhibitor['address']  if not e.address  else e.address
        e.address2  = exhibitor['address2'] if not e.address2 else e.address2
        e.city      = exhibitor['city']     if not e.city     else e.city
        e.state     = exhibitor['state']    if not e.state    else e.state
        e.phone     = exhibitor['phone']    if not e.phone    else e.phone
        e.zip       = exhibitor['zip']      if not e.zip      else e.zip
        e.fax       = exhibitor['fax']      if not e.fax      else e.fax
        e.lines     = exhibitor['lines']    if not e.lines    else e.lines
        e.save()
    return


#        {'username':'', 'password':'', 'first_name':'', 'last_name':'', 'email':'', 'company':'', 'website':'', 'address':'', 'address2':'', 'city':'', 'state':'', 'phone':'', 'fax':'', },
retailers = [
        {'username':'jessica_thompson', 'password':'password', 'first_name':'Jessica', 'last_name':'Thompson', 'email':'jesthompson2010@gmail.com', 'company':'',        'website':'', 'address':'',                  'address2':'', 'city':'',         'state':'',   'zip':'',      'phone':'253-858-1147', 'fax':'', },
        {'username':'reese_prouty',     'password':'password', 'first_name':'Reese',   'last_name':'Prouty',   'email':'',                          'company':'8 Women', 'website':'', 'address':'3614 SE Hawthorne', 'address2':'', 'city':'Portland', 'state':'OR', 'zip':'97214', 'phone':'503-236-8878', 'fax':'', },
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
        r.address   = retailer['address']  if not r.address  else r.address
        r.address2  = retailer['address2'] if not r.address2 else r.address2
        r.city      = retailer['city']     if not r.city     else r.city
        r.state     = retailer['state']    if not r.state    else r.state
        r.phone     = retailer['phone']    if not r.phone    else r.phone
        r.zip       = retailer['zip']      if not r.zip      else r.zip
        r.fax       = retailer['fax']      if not r.fax      else r.fax
        r.save()
    return

shows = [
         {
          'name'       : 'February 2013',
          'late_date'  : datetime.date(2012, 12, 24),
          'closed_date': datetime.date(2013,  1, 24),
          'start_date' : datetime.date(2013,  2, 24),
          'end_date'   : datetime.date(2013,  2, 26),
          },
         ]

def populate_shows(shows):
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
        # must save before add manytomany!
        s.save()
        # !!! I probbaly need some indication in the seed data for which shows they went to, but for now let's do this
        for exhibitor in Exhibitor.objects.all():
            s.exhibitors.add(exhibitor)
        for retailer in Retailer.objects.all():
            s.retailers.add(retailer)

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
