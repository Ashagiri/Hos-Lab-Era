from django.core.management.base import BaseCommand
from accounts.models import User
from accounts.utils import generate_unique_username


class Command(BaseCommand):
    help = (
        "Fixes existing patient/technician accounts whose username is just "
        "a copy of their email address (e.g. 'kritika22@gmail.com'), by "
        "generating a short, readable username from their full name "
        "instead (e.g. 'kritika.sharma'). Login by email keeps working "
        "unchanged -- only the stored username value changes."
    )

    def handle(self, *args, **options):
        accounts = User.objects.filter(
            role__in=['patient', 'technician'], is_superuser=False
        )

        updated_count = 0
        for u in accounts:
            # Only touch accounts where the username is literally the email
            # (or blank) -- leave any already-customised username alone.
            if u.username and u.email and u.username.lower() != u.email.lower():
                continue

            full_name = u.full_name or u.get_full_name() or ''
            new_username = generate_unique_username(full_name, role_prefix=u.role or 'user')

            if new_username != u.username:
                old_username = u.username
                u.username = new_username
                u.save(update_fields=['username'])
                updated_count += 1
                self.stdout.write(
                    self.style.SUCCESS(f"{old_username} -> {new_username}")
                )

        self.stdout.write(self.style.SUCCESS(f"\nDone. {updated_count} username(s) updated."))
