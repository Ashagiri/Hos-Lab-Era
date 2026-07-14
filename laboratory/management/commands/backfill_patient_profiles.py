from django.core.management.base import BaseCommand
from accounts.models import User
from laboratory.models import PatientProfile


class Command(BaseCommand):
    help = "Creates a PatientProfile for any existing patient account that doesn't already have one."

    def handle(self, *args, **options):
        patients = User.objects.filter(role__iexact='patient', is_superuser=False, is_staff=False)

        created_count = 0
        for u in patients:
            u.role = 'patient'
            u.save()

            _, created = PatientProfile.objects.get_or_create(
                user=u,
                defaults={
                    'age': u.age or 0,
                    'gender': (u.gender or 'O')[0].upper() if u.gender else 'O',
                }
            )
            if created:
                created_count += 1
                self.stdout.write(self.style.SUCCESS(f"Created PatientProfile for {u.username}"))
            else:
                self.stdout.write(f"{u.username} already has a PatientProfile - skipped")

        self.stdout.write(self.style.SUCCESS(f"\nDone. {created_count} new patient profile(s) created."))
