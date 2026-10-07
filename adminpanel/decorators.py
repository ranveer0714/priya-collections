from functools import wraps

from django.contrib import messages
from django.shortcuts import redirect
from django.urls import reverse


def admin_staff_required(view_func):
    @wraps(view_func)
    def wrapper(request, *args, **kwargs):
        if request.user.is_authenticated and request.user.is_staff:
            return view_func(request, *args, **kwargs)

        messages.warning(request, 'Please login with a staff account to open the dashboard.')
        login_url = reverse('adminpanel:login')
        return redirect(f'{login_url}?next={request.get_full_path()}')

    return wrapper
