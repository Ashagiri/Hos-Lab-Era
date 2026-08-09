import re
import secrets

from django.contrib.auth import get_user_model


def generate_unique_username(full_name, role_prefix='user'):
    """
    Builds a short, human-readable, unique username from a person's
    full name (e.g. "Kritika Sharma" -> "kritika.sharma"), instead of
    reusing their email address as the username.

    Falls back to a role-based prefix ('patient', 'tech', ...) if no
    usable name is supplied. Appends a numeric suffix on collision.
    """
    User = get_user_model()

    base = (full_name or '').strip().lower()
    base = re.sub(r'[^a-z0-9\s]', '', base)
    base = re.sub(r'\s+', '.', base).strip('.')

    if not base:
        base = role_prefix

    candidate = base
    suffix = 1
    while User.objects.filter(username=candidate).exists():
        suffix += 1
        candidate = f"{base}{suffix}"

    return candidate


def generate_strong_temp_password(length=12):
    """
    Generates a random password that satisfies Django's configured
    AUTH_PASSWORD_VALIDATORS (long, mixed characters) -- used as a
    suggested starting password when an admin creates a staff account,
    so nobody has to type in something like 'test' / '123' by hand.
    """
    alphabet = "abcdefghjkmnpqrstuvwxyzABCDEFGHJKMNPQRSTUVWXYZ23456789!@#$%&*"
    return ''.join(secrets.choice(alphabet) for _ in range(length))
