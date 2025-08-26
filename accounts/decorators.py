# accounts/decorators.py

from django.contrib.auth.decorators import login_required
from django.http import HttpResponseForbidden
from functools import wraps

def admin_required(view_func):
    """
    Decorator for views that requires the user be logged in and have is_admin=True.
    If not, returns 403 Forbidden.
    """
    @wraps(view_func)
    @login_required(login_url='accounts:admin_login')
    def _wrapped_view(request, *args, **kwargs):
        if not getattr(request.user, 'is_admin', False):
            return HttpResponseForbidden("403 Forbidden: Admins only.")
        return view_func(request, *args, **kwargs)
    return _wrapped_view
