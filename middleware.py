from django.http import HttpResponseRedirect
from nwkidsshow.views import get_user
from nwkidsshow.views import password_change_wrapper
# from django.contrib.auth.views import password_change

class ForcePasswordChange(object):

    def process_view(self, request, view, args, kwargs):
        user = get_user(request)  # helper method in my views.py
        # force a redirect to change the password iff
        # - the user was found in the Exhibitor or Retailer database
        # - the user has the flag set to force a change
        # - we're NOT going to the password change page already (infinite redirects!)
        if user and user.must_change_password and view != password_change_wrapper:
            return HttpResponseRedirect('/accounts/password_change/')
        return None
