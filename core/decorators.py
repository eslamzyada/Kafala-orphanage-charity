"""
core/decorators.py — Custom access-control decorators for the Kafala platform.

WHY THIS EXISTS (for graduation defense):
Django's built-in @login_required only checks if the user is authenticated.
We need a second layer that checks if the user has a specific ROLE (Guardian).
This decorator pattern is a clean, reusable alternative to repeating the same
if-check at the top of every view function.
"""
from functools import wraps
from django.shortcuts import redirect
from django.contrib import messages
from django.contrib.auth.decorators import login_required


def guardian_required(view_func):
    """
    Decorator that ensures the request is made by an authenticated user
    who has an associated Guardian profile.

    Security layers:
    1. @login_required — rejects unauthenticated users (redirects to login)
    2. is_superuser check — admins have their own dashboard, block them here
    3. hasattr(user, 'guardian') — confirms a Guardian row exists for this User
       via the OneToOneField reverse relation (Guardian.user → User.guardian)
    """
    @wraps(view_func)
    @login_required(login_url='index')
    def _wrapped(request, *args, **kwargs):
        # Admins should use their own admin dashboard, not the guardian portal.
        if request.user.is_superuser:
            messages.error(request, "هذه اللوحة مخصصة للأوصياء فقط.")
            return redirect('admin_dashboard')

        # Check that this User has a linked Guardian profile.
        # Django auto-creates a reverse accessor called 'guardian' from the
        # Guardian.user OneToOneField. If no Guardian row exists, accessing
        # request.user.guardian would raise RelatedObjectDoesNotExist.
        if not hasattr(request.user, 'guardian'):
            messages.error(request, "ليس لديك صلاحية الوصول لهذه الصفحة.")
            return redirect('index')

        return view_func(request, *args, **kwargs)

    return _wrapped
