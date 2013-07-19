from django.conf.urls import patterns, include, url
from django.contrib.auth.views import login, logout, password_change
from django.views.generic import TemplateView

# Uncomment the next two lines to enable the admin:
from django.contrib import admin
admin.autodiscover()

urlpatterns = patterns('',
    # Examples:
    url(r'^$', 'nwkidsshow.views.home', name='home'),
    # url(r'^nwkidsshow/', include('nwkidsshow.foo.urls')),

    url(r'^dump/$', 'nwkidsshow.views.dump', name='dump'),
    url(r'^seed/$', 'nwkidsshow.views.seed', name='seed'),
    url(r'^add-user/$', 'nwkidsshow.views.add_user', name='adduser'),
    
    url(r'^accounts/login/$',  login, {'template_name':'login.html'}), 
#    url(r'^accounts/logout/$', logout, {'next_page':'logged_out.html'}),
    url(r'^accounts/logout/$', logout, {'next_page':'/advising/logged_out'}),
    url(r'^accounts/password_change/$', 'nwkidsshow.views.password_change_wrapper',
        {'template_name': 'password_change.html',
         'post_change_redirect': '/accounts/profile/'}),
    url(r'^accounts/profile/$', 'nwkidsshow.views.profile', name='profile'),

    url(r'^contact/$', 'nwkidsshow.views.contact', name='contact'),
    url(r'^about/$', 'nwkidsshow.views.about', name='about'),

    url(r'^advising/(?P<advice>\w+)/$', TemplateView.as_view(template_name="advising.html")),

    url(r'^exhibitor/home/$', 'nwkidsshow.views.exhibitor_home', name='exhibitor_home'),
    url(r'^retailer/home/$', 'nwkidsshow.views.retailer_home', name='retailer_home'),

    url(r'^register/$', 'nwkidsshow.views.register', name='register'),

    url(r'^invoices/$', 'nwkidsshow.views.invoices', name='invoices'),
    url(r'^invoice/(?P<show_id>\w+)/$', 'nwkidsshow.views.invoice', name='invoice'),

    url(r'^registrations/$', 'nwkidsshow.views.registrations', name='registrations'),
    url(r'^registered/(?P<show_id>\w+)/$', 'nwkidsshow.views.registered', name='registered'),

    url(r'^lines/$', 'nwkidsshow.views.lines', name='lines'),
    url(r'^edit/$', 'nwkidsshow.views.edit', name='edit'),

    url(r'^report/retailers/$', 'nwkidsshow.views.report_retailers_form', name='report_retailers_form'),
    url(r'^report/retailers/(?P<show_id>\w+)/$', 'nwkidsshow.views.report_retailers', name='report_retailers'),
    url(r'^report/retailers/(?P<show_id>\w+)/xls/$', 'nwkidsshow.views.report_retailers_xls', name='report_retailers_xls'),

    url(r'^report/exhibitors/$', 'nwkidsshow.views.report_exhibitors_form', name='report_exhibitors_form'),
    url(r'^report/exhibitors/(?P<show_id>\w+)/$', 'nwkidsshow.views.report_exhibitors', name='report_exhibitors'),
    url(r'^report/exhibitors/(?P<show_id>\w+)/xls/$', 'nwkidsshow.views.report_exhibitors_xls', name='report_exhibitors_xls'),

    url(r'^report/lines/$', 'nwkidsshow.views.report_exhibitors_form', name='report_exhibitors_form'),
    url(r'^report/lines/(?P<show_id>\w+)/$', 'nwkidsshow.views.report_lines', name='report_lines'),
    url(r'^report/lines/(?P<show_id>\w+)/xls/$', 'nwkidsshow.views.report_lines_xls', name='report_lines_xls'),
    url(r'^exhibitors/(?P<exhibitor_id>\w+)/(?P<show_id>\w+)/$', 'nwkidsshow.views.exhibitor', name='exhibitor'),
    # Uncomment the admin/doc line below to enable admin documentation:
    # url(r'^admin/doc/', include('django.contrib.admindocs.urls')),

    # Uncomment the next line to enable the admin:
    url(r'^admin/', include(admin.site.urls)),
)
