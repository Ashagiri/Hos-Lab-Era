"""
Single source of truth for role-based access control.

Previously every view module (admin.py, staff.py, patient.py,
payment_views.py) re-implemented its own copy of:

    (hasattr(user, 'role') and user.role in [...]) or user.username == 'tech' or user.is_superuser

Having N copies of the same security check is how you end up with one
view that forgets it -- which is exactly what happened to
`reports_list` in staff.py: it had no role check at all, so any
logged-in patient could browse every completed appointment for every
patient in the system just by visiting the technician reports URL.

Everything role-related now lives here. Views should import
`is_admin` / `is_technician` / `is_lab_staff` for read-only checks (e.g.
to toggle what a template shows) and the `role_required(...)` decorator
to actually gate a view.
"""
from functools import wraps

from django.contrib import messages
from django.contrib.auth.decorators import login_required
from django.shortcuts import redirect


def is_technician(user):
    """
    True for accounts flagged with the 'technician' role, plus the
    legacy 'tech' username used by some seeded/demo accounts.
    Superusers are NOT automatically technicians (see is_admin).
    """
    return (hasattr(user, 'role') and user.role == 'technician') or user.username == 'tech'


def is_admin(user):
    """
    True for accounts flagged with the 'admin' role, plus Django
    superusers (so the superuser created via createsuperuser can reach
    the Admin Dashboard without needing its role field hand-edited).

    Technicians are intentionally excluded even if a technician account
    happens to also be flagged is_superuser, so technician accounts are
    routed to the technician dashboard, not the admin one.
    """
    if is_technician(user):
        return False
    return (hasattr(user, 'role') and user.role == 'admin') or user.is_superuser


def is_lab_staff(user):
    """True for anyone allowed to see other patients' lab data: admins or technicians."""
    return is_admin(user) or is_technician(user)


def role_required(check_fn, redirect_to='login', message="Access restricted to authorized profiles."):
    """
    Decorator factory: gates a view behind both login AND a role check.

    Usage:
        @role_required(is_admin)
        def admin_dashboard_view(request): ...

        @role_required(is_lab_staff, redirect_to='dashboard')
        def view_test_requests(request): ...

    `check_fn` is one of is_admin / is_technician / is_lab_staff (or any
    callable taking a user and returning a bool). `redirect_to` lets
    callers keep the existing behaviour of sending rejected patients
    back to their own dashboard instead of the login page.
    """
    def decorator(view_func):
        @login_required
        @wraps(view_func)
        def wrapped(request, *args, **kwargs):
            if not check_fn(request.user):
                messages.error(request, message)
                return redirect(redirect_to)
            return view_func(request, *args, **kwargs)
        return wrapped
    return decorator
