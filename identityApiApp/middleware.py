#---the middle ware code----#

import time
from django.contrib.auth import logout
from django.shortcuts import redirect

#----so that the user is automatically logged out after 30 mins of inactivity---#
class AutoLogoutMiddleware:

    def __init__(self, get_response):
        self.get_response = get_response
        self.timeout = 1800  # 1800 seconds =  30 minutes

    def __call__(self, request):

        if request.user.is_authenticated:
            last_activity = request.session.get("last_activity")

            if last_activity:
                if time.time() - last_activity > self.timeout:
                    logout(request)
                    return redirect("login")

            request.session["last_activity"] = time.time()

        response = self.get_response(request)
        return response

