from django.contrib import admin
from django.urls import path, include
from django.shortcuts import redirect
from django.urls import reverse

def root_redirect(request):
    """
    If you're authenticated as a student, go to your dashboard.
    If you're authenticated as an admin, go to the admin dashboard.
    Otherwise, go to student login.
    """
    user = request.user
    if user.is_authenticated:
        # Admin users go to admin dashboard
        if getattr(user, 'is_admin', False):
            return redirect('accounts:admin_dashboard')
        # Everyone else (students) to student dashboard
        return redirect('accounts:student_dashboard')
    # Anonymous users go to student login
    return redirect('accounts:student_login')


urlpatterns = [
    # Smart root redirect
    path('', root_redirect, name='root_redirect'),

    # Default Django admin site (optional)
    path('django-admin/', admin.site.urls),

    # Account URLs: student & admin auth + dashboards
    path('accounts/', include(('accounts.urls', 'accounts'), namespace='accounts')),

    # Admin positions management under /accounts/admin/positions/
    path('accounts/admin/positions/', include(('positions.urls', 'positions'), namespace='positions')),

    # (Optional) another alias for the admin site
    path('admin/', admin.site.urls),
]
