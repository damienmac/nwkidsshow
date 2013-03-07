from django.conf.urls import patterns, include, url
from django.contrib.auth.views import login, logout

# Uncomment the next two lines to enable the admin:
from django.contrib import admin
admin.autodiscover()

urlpatterns = patterns('',
    # Examples:
    url(r'^$', 'nwkidsshow.views.home', name='home'),
    url(r'^dump/$', 'nwkidsshow.views.dump', name='dump'),
    url(r'^seed/$', 'nwkidsshow.views.seed', name='seed'),
    url(r'^accounts/login/$',  login, {'template_name':'login.html'}), 
    url(r'^accounts/logout/$', logout, {'next_page':'logged_out.html'}),
    url(r'^accounts/profile/$', 'nwkidsshow.views.profile', name='profile'),
    # url(r'^nwkidsshow/', include('nwkidsshow.foo.urls')),

    # Uncomment the admin/doc line below to enable admin documentation:
    # url(r'^admin/doc/', include('django.contrib.admindocs.urls')),

    # Uncomment the next line to enable the admin:
    url(r'^admin/', include(admin.site.urls)),
)
