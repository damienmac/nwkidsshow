# Django settings for nwkidsshow project.
import os

BASE_DIR = (os.path.abspath(os.path.dirname(__file__)) + os.sep).replace('\\','/')

running_in_prod = False
if os.getenv('SERVER_SOFTWARE', '').startswith('Google App Engine') or os.getenv('SETTINGS_MODE') == 'prod':
    running_in_prod = True

DEBUG = True
if running_in_prod:
    DEBUG = False

TEMPLATE_DEBUG = DEBUG

#A tuple that lists people who get code error notifications.
# When DEBUG=False and a view raises an exception, Django will
# email these people with the full exception information.
ADMINS = (
    # ('Your Name', 'your_email@example.com'),
)

ALLOWED_HOSTS = [
    'www.nwkidsshow.com',
    'www.cakidsshow.com',
]

MANAGERS = ADMINS

if running_in_prod:
    # Running on production App Engine, so use a Google Cloud SQL database.:
    DATABASES = {
        'default': {
            'ENGINE': 'google.appengine.ext.django.backends.rdbms',
            'INSTANCE': 'nwkidsshow.com:nwkidsshowdb:instance1',
            'NAME': 'nwkidsshowdb1',
        }
    }
else:
    # Running in development, so use a local MySQL database
    DATABASES = {
        'default': {
            'ENGINE': 'django.db.backends.mysql',
            'USER': 'root',
            'PASSWORD': '',
            'HOST': 'localhost',
            # 'NAME': 'nwkidsshowdevdb',
            'NAME': 'nwkidsshowdb1',
        }
    }

# Local time zone for this installation. Choices can be found here:
# http://en.wikipedia.org/wiki/List_of_tz_zones_by_name
# although not all choices may be available on all operating systems.
# In a Windows environment this must be set to your system time zone.
TIME_ZONE = 'America/Los_Angeles'

# Language code for this installation. All choices can be found here:
# http://www.i18nguy.com/unicode/language-identifiers.html
LANGUAGE_CODE = 'en-us'

SITE_ID = 1

# If you set this to False, Django will make some optimizations so as not
# to load the internationalization machinery.
USE_I18N = True

# If you set this to False, Django will not format dates, numbers and
# calendars according to the current locale.
USE_L10N = True

# If you set this to False, Django will not use timezone-aware datetimes.
USE_TZ = True

# Absolute filesystem path to the directory that will hold user-uploaded files.
# Example: "/home/media/media.lawrence.com/media/"
MEDIA_ROOT = ''

# URL that handles the media served from MEDIA_ROOT. Make sure to use a
# trailing slash.
# Examples: "http://media.lawrence.com/media/", "http://example.com/media/"
MEDIA_URL = ''

# Absolute path to the directory static files should be collected to.
# Don't put anything in this directory yourself; store your static files
# in apps' "static/" subdirectories and in STATICFILES_DIRS.
# Example: "/home/media/media.lawrence.com/static/"
# STATIC_ROOT = ''
STATIC_ROOT = BASE_DIR + 'static'

# URL prefix for static files.
# Example: "http://media.lawrence.com/static/"
STATIC_URL = '/static/'

# Additional locations of static files
STATICFILES_DIRS = (
    # Put strings here, like "/home/html/static" or "C:/www/django/static".
    # Always use forward slashes, even on Windows.
    # Don't forget to use absolute paths, not relative paths.
    ('css',    BASE_DIR + 'static/css'),
    ('images', BASE_DIR + 'static/images'),
)
#print os.path.join(os.path.dirname(__file__),'static/images').replace('\\','/')

# List of finder classes that know how to find static files in
# various locations.
STATICFILES_FINDERS = (
    'django.contrib.staticfiles.finders.FileSystemFinder',
    'django.contrib.staticfiles.finders.AppDirectoriesFinder',
#    'django.contrib.staticfiles.finders.DefaultStorageFinder',
)

# Make this unique, and don't share it with anybody.
SECRET_KEY = 'eusas6^@n@h*c*60yf$=)(9hlae1s)mfimx85p4437@8+^q+44'

# List of callables that know how to import templates from various sources.
TEMPLATE_LOADERS = (
    'django.template.loaders.filesystem.Loader',
    'django.template.loaders.app_directories.Loader',
#     'django.template.loaders.eggs.Loader',
)

MIDDLEWARE_CLASSES = (
    'django.middleware.common.CommonMiddleware',
    'django.contrib.sessions.middleware.SessionMiddleware',
    'django.middleware.csrf.CsrfViewMiddleware',
    'django.contrib.auth.middleware.AuthenticationMiddleware', # must come after SessionMiddleware
    'django.contrib.messages.middleware.MessageMiddleware',
    'nwkidsshow.middleware.ForcePasswordChange',
    # Uncomment the next line for simple clickjacking protection:
    # 'django.middleware.clickjacking.XFrameOptionsMiddleware',
)

ROOT_URLCONF = 'nwkidsshow.urls'

# Python dotted path to the WSGI application used by Django's runserver.
# WSGI_APPLICATION = 'nwkidsshow.wsgi.application'

TEMPLATE_DIRS = (
    # Put strings here, like "/home/html/django_templates" or "C:/www/django/templates".
    # Always use forward slashes, even on Windows.
    # Don't forget to use absolute paths, not relative paths.
#    'C:/Users/Damien/PycharmProjects/nwkidsshow/nwkidsshow/templates',
    'nwkidsshow/templates',
)

INSTALLED_APPS = (
    'django.contrib.auth',
    'django.contrib.contenttypes',
    'django.contrib.sessions',
#    'django.contrib.sites',
#    'django.contrib.messages',
    'django.contrib.staticfiles',
    # Uncomment the next line to enable the admin:
     'django.contrib.admin',
    # Uncomment the next line to enable admin documentation:
    # 'django.contrib.admindocs',
    'django.contrib.humanize',
    'nwkidsshow',
)

# A sample logging configuration. The only tangible logging
# performed by this configuration is to send an email to
# the site admins on every HTTP 500 error when DEBUG=False.
# See http://docs.djangoproject.com/en/dev/topics/logging for
# more details on how to customize your logging configuration.
LOGGING = {
    'version': 1,
    'disable_existing_loggers': False,
    'filters': {
        'require_debug_false': {
            '()': 'django.utils.log.RequireDebugFalse'
        }
    },
    'handlers': {
        'mail_admins': {
            'level': 'ERROR',
            'filters': ['require_debug_false'],
            'class': 'django.utils.log.AdminEmailHandler'
        }
    },
    'loggers': {
        'django.request': {
            'handlers': ['mail_admins'],
            'level': 'ERROR',
            'propagate': True,
        },
    }
}

###########################################################
# some line in the yaml file has:
#   version: 6
# in it, I want it in my template context
###########################################################

# here's a method to get that number out of the yaml
# uses NO REGEX on purpose.
# I am using just INT versions right now, so return an INT not FLOAT
def get_app_yaml_version():
    version = '#' # some bad default
    try:
        yaml = open(BASE_DIR+'../app.yaml', 'r')
    except IOError as e:
        print "I/O error({0}): {1}".format(e.errno, e.strerror)
        return version
    while True:
        line = yaml.readline()
        if not line:
            break
        if line.startswith('version:'):
            version_string = line.split(':')[-1]
            try:
                version = int(version_string)
            except ValueError:
                print 'Could not convert "%s" from app.yaml to int()' % version_string
            break
    yaml.close()
    return version

# set it to a settings variable
VERSION = get_app_yaml_version()

# If you ever want to get ALL the capitalized settings vars into the context, try this (untested!)
# import re
# _context = {}
# local_context = locals()
# for (k,v) in local_context.items():
#     if re.search('^[A-Z0-9_]+$',k):
#         _context[k] = str(v)

# but for now I just want VERSION
_context = {
    'VERSION': str(VERSION),
}

def settings_context(request):
    return _context

#CAREFUL: adding my own, but don't squash the defaults!
from django.conf import global_settings
TEMPLATE_CONTEXT_PROCESSORS = global_settings.TEMPLATE_CONTEXT_PROCESSORS + (
    'nwkidsshow.settings.settings_context', # this comma is important
    'nwkidsshow.views.venue_context', # this comma is important
)
###########################################################
